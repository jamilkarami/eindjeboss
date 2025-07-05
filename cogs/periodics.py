import json
import logging as lg
import os
from datetime import date, datetime

import dateparser
import discord
import requests
from aiocron import crontab
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from bot import Eindjeboss
from util.util import get_file, load_json_file
from util.vars.eind_vars import PERIODIC_MESSAGES_FILE
from util.vars.periodics import ALERT_DT, PSV_DT, WEATHER_DT

FILE_DIR = os.getenv("FILE_DIR")

# Weather
OW = os.getenv("OPENWEATHER_API_KEY")
CITY_QUERY = "EINDHOVEN, NL"
CITY_NAME = "Eindhoven"
BASE_URL = "http://api.openweathermap.org/data/2.5/forecast?"
UNIT = "metric"

WEATHER_FILES_DIR = FILE_DIR + "/weather_images/"

BASE_FILE = "base.png"
MASK_FILE = "mask.png"
CLOUD_FILE = "cloud.png"
RAINY_FILE = "rainy.png"
SNOWY_FILE = "snowy.png"
STORM_FILE = "storm.png"
CLEAR_FILE = "clear.png"

WEATHER_IMGS = {
    "Fog": CLOUD_FILE,
    "Clouds": CLOUD_FILE,
    "Rain": RAINY_FILE,
    "Drizzle": RAINY_FILE,
    "Snow": SNOWY_FILE,
    "Thunderstorm": STORM_FILE,
    "Clear": CLEAR_FILE,
}
WEATHER_OUTPUT_FILE = "weather.png"

FONT = FILE_DIR + "/fonts/coolvetica_rg.otf"
FONT_IT = FILE_DIR + "/fonts/coolvetica_rg_it.otf"
SEPARATOR = 160
IMG_SIZE = (960, 400)

SIZE_TITLE = 32
FONT_SUBTTL = 16
SZ_SML_TTL = 14
SIZE_VALUE = 28

# PSV games
STADION_ID = int(os.getenv("STADION_ID"))
PSV_TEAM_ID = os.getenv("PSV_TEAM_ID")
FIXTURES_URL = os.getenv("FOOTBALL_API_FIXTURES_URL")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
X_RAPID_API_HOST = os.getenv("X_RAPID_API_HOST")
MATCH_STR = (
    "## ⚽ **Today's Match at Philips Stadion <:psv:1146529553238478878>** ⚽\n\n"
    "**%s** vs **%s**\n"
    "🏆 **Competition:** %s\n"
    "🕐 **Kick-off:** %s\n\n"
    "⚠️ **Traffic Warning:** Expect heavy traffic around the stadium area."
)

WARNING_SIREN_MSG = (
    "## 🚨 **Monthly Siren Test** 🚨\n\n"
    "📢 The public warning sirens will be tested today at **12:00**.\n"
    "🔊 This is a **routine monthly test** - no action required.\n"
    "⏰ Duration: Approximately 1 minute\n\n"
    "ℹ️ *This test ensures the emergency warning system is working properly.*"
)
WARNING_SIREN_LINK = (
    "https://www.government.nl/topics/counterterrorism-and-"
    "national-security/question-and-answer/public-warning-s"
    "irens"
)
WARNING_SIREN_BUTTON_LABEL = "Click here for more information"


class Periodics(commands.Cog):

    def __init__(self, bot: Eindjeboss):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")
        await self.schedule_periodic_messages()
        lg.info("Scheduling periodic messages")
        crontab(WEATHER_DT, func=self.send_weather_forecast, start=True)
        crontab(PSV_DT, func=self.check_psv_game, start=True)
        crontab(ALERT_DT, func=self.send_siren_alert, start=True)

    async def schedule_periodic_messages(self):
        guild_id = os.getenv("GUILD_ID")
        guild = await self.bot.fetch_guild(guild_id)
        periodics = load_json_file(get_file(PERIODIC_MESSAGES_FILE))
        cnt = len(periodics.keys())
        for periodic in periodics.keys():
            vals = periodics[periodic]

            msg_time = vals["time"]
            msg_channel = vals["channel"]
            msg = vals["message"]

            crontab(
                msg_time,
                func=self.send_periodic_message,
                args=(msg, msg_channel, guild),
                start=True,
            )
        lg.info(f"[{__name__}] Scheduled {cnt} periodic message{'s'[:cnt ^ 1]}")

    async def send_siren_alert(self):
        channel_id = await self.bot.get_setting("lounge_channel_id")
        channel = await self.bot.fetch_channel(channel_id)
        if datetime.today().weekday() == 0:
            view = discord.ui.View()
            view.add_item(
                discord.ui.Button(
                    label=WARNING_SIREN_BUTTON_LABEL,
                    style=discord.ButtonStyle.url,
                    url=WARNING_SIREN_LINK,
                )
            )
            await channel.send(WARNING_SIREN_MSG, view=view)
            lg.info("Sent siren warning")

    async def send_periodic_message(self, message, channel_id, guild):
        channel = await guild.fetch_channel(channel_id)
        await channel.send(message)

    async def send_weather_forecast(self):
        channel_id = await self.bot.get_setting("lounge_channel_id")
        today = datetime.today().strftime("%d-%m-%Y")
        title = f"Weather in {CITY_NAME} Today ({today})"
        channel = await self.bot.fetch_channel(channel_id)
        weather_url = f"{BASE_URL}q={CITY_QUERY}&appid={OW}&cnt=6&units={UNIT}"
        response = requests.get(weather_url)
        weather_info = response.json()

        img = Image.new("RGBA", IMG_SIZE, (0, 0, 0, 0))

        weather_details = []

        for itm in weather_info["list"]:
            cond = itm["weather"][0]["main"]
            desc = itm["weather"][0]["description"].capitalize()
            temp = str(round(itm["main"]["temp"])) + "°"
            feel = str(round(itm["main"]["feels_like"])) + "°"
            wind = str(round(itm["wind"]["speed"] * 3.6)) + " km/h"
            time = itm["dt_txt"][-8:-3]

            weather_details.append([cond, desc, temp, feel, wind, time])

        last_cond = ""
        offset = 0

        for _, data in enumerate(weather_details):

            if data[0] != last_cond:
                last_cond = data[0]
                img_file_name = WEATHER_FILES_DIR + WEATHER_IMGS.get(data[0])

                with Image.open(img_file_name, "r").convert("RGBA") as im:
                    img.paste(im, (offset, 0))

                if offset:
                    box = (offset - 15, 0, offset + 15, 400)
                    to_blur = img.crop(box)
                    for i in range(8):
                        to_blur = to_blur.filter(ImageFilter.BLUR)
                    img.paste(to_blur, box)

            info_img = self.make_hour_info(data, True)
            img.paste(info_img, (offset, 0), info_img)
            offset = offset + SEPARATOR

        trs = Image.new("RGBA", IMG_SIZE, (0, 0, 0, 0))
        mask = Image.open(WEATHER_FILES_DIR + MASK_FILE, "r").convert("L")
        img.putalpha(mask)
        trs.paste(img, (0, 0), img)
        trs.save(WEATHER_OUTPUT_FILE)

        await channel.send(title, file=discord.File(WEATHER_OUTPUT_FILE))
        os.remove(WEATHER_OUTPUT_FILE)
        lg.info("Sent daily weather forecast")

    def draw_text(self, draw: ImageDraw, text, pos, fill, font, text_size):
        font = ImageFont.truetype(font, text_size)
        draw.text(pos, text=text, anchor="mm", fill=fill, font=font)

    def make_hour_info(self, info, blurred) -> Image:
        txt_img = Image.new("RGBA", (160, 400), (0, 0, 0, 0))

        x = 80
        y = 50
        color = "black" if blurred else "white"

        draw = ImageDraw.Draw(txt_img)

        self.draw_text(draw, info[5], (x, y), color, FONT, SIZE_TITLE)
        y = y + 30
        self.draw_text(draw, info[1].title(), (x, y), color, FONT, FONT_SUBTTL)
        y = y + 70
        self.draw_text(draw, "Temperature", (x, y), color, FONT_IT, SZ_SML_TTL)
        y = y + 25
        self.draw_text(draw, info[2], (x, y), color, FONT, SIZE_VALUE)
        y = y + 45
        self.draw_text(draw, "Feels Like", (x, y), color, FONT_IT, SZ_SML_TTL)
        y = y + 25
        self.draw_text(draw, info[3], (x, y), color, FONT, SIZE_VALUE)
        y = y + 45
        self.draw_text(draw, "Wind Speed", (x, y), color, FONT_IT, SZ_SML_TTL)
        y = y + 25
        self.draw_text(draw, info[4], (x, y), color, FONT, SIZE_VALUE)

        if blurred:
            for i in range(3):
                txt_img = txt_img.filter(ImageFilter.BLUR)
            txt_img_mrg = self.make_hour_info(info, False)
            txt_img.paste(txt_img_mrg, (0, 0), txt_img_mrg)
            return txt_img

        return txt_img

    async def check_psv_game(self):
        today = date.today()

        tz = await self.bot.get_setting("timezone")
        season_year = today.year - 1 if today.month < 7 else today.year

        query_string = {
            "season": season_year,
            "timezone": tz,
            "date": today.strftime("%Y-%m-%d"),
            "venue": int(STADION_ID),
        }
        channel_id = await self.bot.get_setting("lounge_channel_id")
        channel = await self.bot.fetch_channel(channel_id)

        headers = {
            "X-RapidAPI-Key": FOOTBALL_API_KEY,
            "X-RapidAPI-Host": X_RAPID_API_HOST,
        }

        response = requests.request(
            "GET", FIXTURES_URL, headers=headers, params=query_string
        )
        content = json.loads(response.content)

        if not content["response"]:
            return

        home = content["response"][0]["teams"]["home"]["name"]
        away = content["response"][0]["teams"]["away"]["name"]
        competition = content["response"][0]["league"]["name"]
        dt = content["response"][0]["fixture"]["date"]
        match_time = dateparser.parse(dt).strftime("%H:%M")

        warning_msg = MATCH_STR % (
            home,
            away,
            competition,
            match_time,
        )
        lg.info("There is match playing at Philips Stadion today.")
        await channel.send(warning_msg)


async def setup(client: Eindjeboss):
    await client.add_cog(Periodics(client))
