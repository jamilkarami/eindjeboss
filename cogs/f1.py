import logging as lg
from datetime import datetime, timedelta

import discord
import pytz
import requests
from discord import app_commands
from discord.ext import commands

from bot import Eindjeboss

CURRENT_F1 = "http://ergast.com/api/f1/current.json"


class F1(commands.Cog):

    def __init__(self, bot: Eindjeboss):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name="nextf1race")
    async def nextf1race(self, interaction: discord.Interaction):
        next_race = self.get_next_f1_race()
        if not next_race:
            await interaction.response.send_message(
                "The %s F1 season is over. Wait for the next one."
                % datetime.now().strftime('%Y'), ephemeral=True)
            return

        title = "%s %s" % (next_race['season'], next_race['raceName'])
        times = self.get_session_times(next_race)

        embed = discord.Embed(title=title, url=next_race['url'],
                              color=discord.Color.red())
        for time in times:
            embed.add_field(name=times[time],
                            value=time.strftime('%d/%m at %H:%M'),
                            inline=False)

        await interaction.response.send_message(embed=embed)
        lg.info('Sent next F1 race information to %s'
                % interaction.user.name)

    def get_session_times(self, data):
        first_practice = data.get('FirstPractice')
        second_practice = data.get('SecondPractice')
        third_practice = data.get('ThirdPractice')
        sprint = data.get('Sprint')
        qualifying = data.get('Qualifying')
        race = {'date': data['date'], 'time': data['time']}

        times_local = {'First Practice': first_practice,
                       'Second Practice': second_practice,
                       'Third Practice': third_practice,
                       'Sprint': sprint,
                       'Qualifying': qualifying,
                       'Race': race}
        times_ams = self.get_times_ams(times_local)
        times_ams = {k: times_ams[k] for k in sorted(times_ams)}
        return times_ams

    def get_times_ams(self, times_local):
        tz_local = pytz.timezone('UTC')
        tz_ams = pytz.timezone('Europe/Amsterdam')
        times_ams = {}
        for k, v in times_local.items():
            if v:
                time_str = '%s %s' % (v['date'], v['time'])
                time_ams = tz_local.localize(
                    datetime.strptime(
                        time_str, '%Y-%m-%d %H:%M:%SZ')).astimezone(tz_ams)
                times_ams[time_ams] = k

        return times_ams

    def get_next_f1_race(self):
        data = requests.get(CURRENT_F1).json()
        for race in data['MRData']['RaceTable']['Races']:
            rc_tm = f"{race['date']} {race['time']}"
            rc_tm_dt = datetime.strptime(rc_tm, "%Y-%m-%d %H:%M:%SZ")
            now = datetime.now()
            if rc_tm_dt + timedelta(hours=2) > now:
                return race
        return None


async def setup(client: commands.Bot):
    await client.add_cog(F1(client))
