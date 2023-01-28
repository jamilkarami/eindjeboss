import discord
import logging
import os
import requests
import dateparser
import json
from aiocron import crontab
from datetime import datetime, date
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from table2ascii import table2ascii as t2a, PresetStyle
from util.util import load_json_file, get_file
from util.vars.periodic_reminders import WEATHER_DT, PSV_DT
from util.vars.eind_vars import PERIODIC_MESSAGES_FILE

FILE_DIR = os.getenv('FILE_DIR')

# Weather
CHANNEL_ID = int(os.getenv("ENGLISH_CHANNEL_ID"))
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
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

WEATHER_IMGS = {'Fog': CLOUD_FILE, 'Clouds': CLOUD_FILE, 'Rain': RAINY_FILE, 'Drizzle': RAINY_FILE, 'Snow': SNOWY_FILE, 'Thunderstorm': STORM_FILE, 'Clear': CLEAR_FILE}
WEATHER_OUTPUT_FILE = "weather.png"

FONT = FILE_DIR + "/fonts/coolvetica_rg.otf"
FONT_ITALIC = FILE_DIR + "fonts/coolvetica_rg_it.otf"
SEPARATOR = 160
IMG_SIZE = (960,400)

SIZE_TITLE = 32
SIZE_SUBTITLE = 16
SIZE_SMALL_TITLE = 14
SIZE_VALUE = 28

# PSV games
PSV_TEAM_ID = os.getenv("PSV_TEAM_ID")
FIXTURES_URL = os.getenv("FOOTBALL_API_FIXTURES_URL")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
X_RAPID_API_HOST = os.getenv("X_RAPID_API_HOST")


class Periodics(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"[{__name__}] Cog is ready")
        await self.schedule_periodic_messages()
        logging.info("Scheduling periodic messages")
        crontab(WEATHER_DT, func=self.send_weather_forecast, start=True)
        crontab(PSV_DT, func=self.check_psv_game, start=True)

    async def schedule_periodic_messages(self):
        guild_id = os.getenv("GUILD_ID")
        guild = await self.client.fetch_guild(guild_id)
        periodics = load_json_file(get_file(PERIODIC_MESSAGES_FILE))
        count = len(periodics.keys())
        for periodic in periodics.keys():
            vals = periodics[periodic]

            msg_time = vals['time']
            msg_channel = vals['channel']
            msg = vals['message']

            crontab(msg_time, func=self.send_periodic_message,
                    args=(msg, msg_channel, guild), start=True)
        logging.info(
            f"[{__name__}] Scheduled {count} periodic message{'s'[:count ^ 1]}")

    async def send_periodic_message(self, message, channel_id, guild):
        channel = await guild.fetch_channel(channel_id)
        await channel.send(message)

    async def send_weather_forecast(self):
        today = datetime.today().strftime('%d-%m-%Y')
        title = f"Weather in {CITY_NAME} Today ({today})"
        channel = await self.client.fetch_channel(CHANNEL_ID)
        weather_url = f"{BASE_URL}q={CITY_QUERY}&appid={OPENWEATHER_API_KEY}&cnt=6&units={UNIT}"
        response = requests.get(weather_url)
        weather_info = response.json()
        
        img = Image.new('RGBA', IMG_SIZE, (0,0,0,0))

        weather_details = []

        for itm in weather_info['list']:
            cond = itm['weather'][0]['main']
            desc = itm['weather'][0]['description'].capitalize()
            temp = str(round(itm['main']['temp'])) + "°"
            feel = str(round(itm['main']['feels_like'])) + "°"
            wind = str(round(itm['wind']['speed'])) + " km/h"
            time = itm['dt_txt'][-8:-3]

            weather_details.append([cond,desc,temp,feel,wind,time])

        last_cond = ""
        offset = 0

        for idx, data in enumerate(weather_details):

            if data[0] != last_cond:
                last_cond = data[0]
                img_file_name = WEATHER_FILES_DIR + WEATHER_IMGS.get(data[0])

                with Image.open(img_file_name, 'r').convert('RGBA') as im:
                        img.paste(im, (offset,0))

                if offset:
                    box = (offset-15, 0, offset+15, 400)
                    to_blur = img.crop(box)
                    for i in range(8):
                        to_blur = to_blur.filter(ImageFilter.BLUR)
                    img.paste(to_blur, box)

            info_img = self.make_hour_info(data, True)
            img.paste(info_img, (offset,0), info_img)
            offset = offset + SEPARATOR

        trs = Image.new('RGBA', IMG_SIZE, (0,0,0,0))
        mask = Image.open(WEATHER_FILES_DIR + MASK_FILE, 'r').convert('L')
        img.putalpha(mask)
        trs.paste(img, (0,0), img)
        trs.save(WEATHER_OUTPUT_FILE)

        await channel.send(title, file=discord.File(WEATHER_OUTPUT_FILE))
        os.remove(WEATHER_OUTPUT_FILE)

    def draw_text(self, draw: ImageDraw, text, position, fill, font_name, text_size):
        font = ImageFont.truetype(font_name, text_size)
        draw.text((position), text=text, anchor="mm", fill=fill, font=font)

    def make_hour_info(self, info, blurred) -> Image:
        txt_img = Image.new('RGBA', (160,400), (0,0,0,0))

        x = 80 if blurred else 80
        y = 50 if blurred else 50
        color = "black" if blurred else "white"


        draw = ImageDraw.Draw(txt_img)

        self.draw_text(draw, info[5], (x,y), color, FONT, SIZE_TITLE)
        y = y + 30
        self.draw_text(draw, info[1].title(), (x,y), color, FONT, SIZE_SUBTITLE)
        y = y + 70
        self.draw_text(draw, "Temperature", (x,y), color, FONT_ITALIC, SIZE_SMALL_TITLE)
        y = y + 25
        self.draw_text(draw, info[2], (x,y), color, FONT, SIZE_VALUE)
        y = y + 45
        self.draw_text(draw, "Feels Like", (x,y), color, FONT_ITALIC, SIZE_SMALL_TITLE)
        y = y + 25
        self.draw_text(draw, info[3], (x,y), color, FONT, SIZE_VALUE)
        y = y + 45
        self.draw_text(draw, "Wind Speed", (x,y), color, FONT_ITALIC, SIZE_SMALL_TITLE)
        y = y + 25
        self.draw_text(draw, info[4], (x,y), color, FONT, SIZE_VALUE)

        if blurred:
            for i in range(3):
                txt_img = txt_img.filter(ImageFilter.BLUR)
            txt_img_mrg = self.make_hour_info(info, False)
            txt_img.paste(txt_img_mrg, (0,0), txt_img_mrg)
            return txt_img

        return txt_img

    async def check_psv_game(self):
        today = date.today().strftime('%Y-%m-%d')

        query_string = {"season": "2022", "team": PSV_TEAM_ID,
                        "timezone": "Europe/Amsterdam", "from": today, "to": today}
        channel = await self.client.fetch_channel(CHANNEL_ID)

        headers = {
            "X-RapidAPI-Key": FOOTBALL_API_KEY,
            "X-RapidAPI-Host": X_RAPID_API_HOST
        }

        response = requests.request(
            "GET", FIXTURES_URL, headers=headers, params=query_string)
        content = json.loads(response.content)

        if not content['response']:
            logging.info("PSV is not playing today.")
            return

        if str(content['response'][0]['teams']['home']['id']) != PSV_TEAM_ID:
            logging.info("PSV is playing today, but not at home")
            return

        dt = content['response'][0]['fixture']['date']

        match_time = dateparser.parse(dt).strftime("%H:%M")
        opponent = content['response'][0]['teams']['away']['name']

        logging.info("PSV is playing in Philips Stadion today. Sending notice to English channel.")
        await channel.send(f"**PSV Eindhoven** will be playing against **{opponent}** in **Philips Stadion** today at "
                           f"**{match_time}**. Expect heavy traffic around the stadium.")


async def setup(bot):
    await bot.add_cog(Periodics(bot))
