from discord.ext import commands
import requests
import os
import logging
import discord
from aiocron import crontab
from util.vars.periodic_reminders import WEATHER_DT
from util.vars.eind_vars import *
from table2ascii import table2ascii as t2a, PresetStyle
from datetime import datetime

CHANNEL_ID = int(os.getenv("WEATHER_CHANNEL_ID"))
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
CITY = "EINDHOVEN, NL"
BASE_URL = "http://api.openweathermap.org/data/2.5/forecast?"
UNIT = "metric"

CONDITION_EMOJIS = {
    'Rain': WEATHER_EMOJI_CLOUDS_RAIN,
    'Clouds': WEATHER_EMOJI_CLOUDS,
    'Clear': WEATHER_EMOJI_SUN,
    'Drizzle': WEATHER_EMOJI_CLOUDS_RAIN,
    'Thunderstorm': WEATHER_EMOJI_STORM,
    'Snow': WEATHER_EMOJI_SNOW,
}


class Weather(commands.Cog):

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{__name__} Cog is ready")
        crontab(WEATHER_DT, func=self.schedule_weather, start=True)

    def __init__(self, bot: discord.Client):
        self.bot = bot

    async def schedule_weather(self):
        today = datetime.today().strftime('%d-%m-%Y')
        embed_title = f"Weather in Eindhoven Today ({today})"
        channel = await self.bot.fetch_channel(CHANNEL_ID)
        weather_url = f"{BASE_URL}q={CITY}&appid={OPENWEATHER_API_KEY}&cnt=6&units={UNIT}"
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
        return


async def setup(bot):
    await bot.add_cog(Weather(bot))
