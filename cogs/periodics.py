import discord
import logging
import os
import requests
import dateparser
import random
from discord.ext import commands
from datetime import datetime, date
from util.util import *
from aiocron import crontab
from util.vars.periodic_reminders import *
from util.vars.eind_vars import *
from table2ascii import table2ascii as t2a, PresetStyle


# Weather
CHANNEL_ID = int(os.getenv("ENGLISH_CHANNEL_ID"))
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
CITY_QUERY = "EINDHOVEN, NL"
CITY_NAME = "Eindhoven"
BASE_URL = "http://api.openweathermap.org/data/2.5/forecast?"
UNIT = "metric"

# PSV games
PSV_TEAM_ID = os.getenv("PSV_TEAM_ID")
FIXTURES_URL = os.getenv("FOOTBALL_API_FIXTURES_URL")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
X_RAPID_API_HOST = os.getenv("X_RAPID_API_HOST")

# Graggy
GRAGGY_FILE = "graggy.json"

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
        crontab(GRAGGY_DT, func=self.send_graggy_quote, start=True)

    async def send_graggy_quote(self):
        guild_id = os.getenv("GUILD_ID")
        guild = await self.client.fetch_guild(guild_id)
        quotes = load_json_file(get_file(GRAGGY_FILE))
        graggy_channel = os.getenv("GRAGGY_CHANNEL_ID")

        random.seed()
        quote, date = random.choice(list(quotes.items()))
        msg = f"\"{quote}\" -Graggy, {date}"

        await self.send_periodic_message(msg, graggy_channel, guild)

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
        count
        logging.info(
            f"[{__name__}] Scheduled {count} periodic message{'s'[:count ^ 1]}")

    async def send_periodic_message(self, message, channel_id, guild):
        channel = await guild.fetch_channel(channel_id)
        await channel.send(message)

    async def send_weather_forecast(self):
        today = datetime.today().strftime('%d-%m-%Y')
        embed_title = f"Weather in {CITY_NAME} Today ({today})"
        channel = await self.client.fetch_channel(CHANNEL_ID)
        weather_url = f"{BASE_URL}q={CITY_QUERY}&appid={OPENWEATHER_API_KEY}&cnt=6&units={UNIT}"
        response = requests.get(weather_url)
        data = response.json()
        lst = data['list']

        body = []

        for itm in lst:
            dt = itm['dt_txt'][-8:-3]
            temperature = round(int(itm['main']['temp']))
            condition = itm['weather'][0]['description'].capitalize()

            body.append([dt, temperature, condition])

        output = t2a(
            header=["Time", "Temp.", "Cond."],
            body=body,
            style=PresetStyle.ascii_borderless
        )

        embed = discord.Embed(title=embed_title, description=f"```{output}```")
        await channel.send(embed=embed)

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
        await channel.send(f"**PSV Eindhoven** will be playing against **{opponent}** in **Philips Stadion** today at **{match_time}**. Expect heavy traffic around the stadium.")


async def setup(bot):
    await bot.add_cog(Periodics(bot))
