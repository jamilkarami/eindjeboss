import logging as lg
from datetime import datetime
from typing import Any

import discord
import pytz
import requests
from discord import app_commands
from discord.ext import commands

from bot import Eindjeboss

CURRENT_F1 = "http://ergast.com/api/f1/{year}.json"
CURRENT_ROUND = "https://ergast.com/api/f1/{year}/next.json"


class F1(commands.Cog):

    def __init__(self, bot: Eindjeboss):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name="nextf1race")
    async def nextf1race(self, interaction: discord.Interaction):
        current_round = get_current_round() - 1
        races = get_races()
        embed = F1Embed(races[current_round], is_current=True)
        await interaction.response.send_message(embed=embed, view=F1View(
            get_races(), current_round))


class F1View(discord.ui.View):

    def __init__(self, races, idx: int):
        super().__init__(timeout=300.0)
        self.races = races
        self.idx = idx
        self.add_item(MoveButton(discord.ButtonStyle.red, "Prev", -1))
        self.add_item(MoveButton(discord.ButtonStyle.green, "Next", 1))

    def get_race_at_idx(self):
        return self.races[self.idx]

    def update_idx(self, update):
        self.idx = (self.idx + update) % len(self.races)

    async def on_timeout(self) -> None:
        self.clear_items()

    async def update_msg(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=F1Embed(self.get_race_at_idx(),
                          is_current=(self.idx == get_current_round() - 1)))


class F1Embed(discord.Embed):

    def __init__(self, race, is_current: bool = False):
        color = discord.Color.red() if not is_current else discord.Color.green()
        super().__init__(color=color,
                         title=f"{race['raceName']} ({datetime.now().year})")
        details = get_times(race)
        for k, v in details.items():
            self.add_field(name=v,
                           value=k.strftime("%d/%m at %H:%M"), inline=False)


class MoveButton(discord.ui.Button):

    def __init__(self, style, label, update):
        super().__init__(style=style, label=label)
        self.update = update

    async def callback(self, interaction: discord.Interaction) -> Any:
        self.view.update_idx(self.update)
        await self.view.update_msg(interaction)


def get_races():
    data = requests.get(CURRENT_F1.format(year = datetime.today().year)).json()
    return data['MRData']['RaceTable']['Races']


def get_current_round() -> int:
    data = requests.get(CURRENT_ROUND.format(year = datetime.today().year)).json()
    return int(data['MRData']['RaceTable']['Races'][0]["round"])


def get_times(race_data):
    first_practice = race_data.get('FirstPractice')
    second_practice = race_data.get('SecondPractice')
    third_practice = race_data.get('ThirdPractice')
    sprint = race_data.get('Sprint')
    qualifying = race_data.get('Qualifying')
    race = {'date': race_data['date'], 'time': race_data['time']}

    times_local = {'First Practice': first_practice,
                   'Second Practice': second_practice,
                   'Third Practice': third_practice,
                   'Sprint': sprint,
                   'Qualifying': qualifying,
                   'Race': race}
    times_ams = get_times_tz(times_local)
    times_ams = {k: times_ams[k] for k in sorted(times_ams)}
    return times_ams


def get_times_tz(times_local):
    tz_local = pytz.timezone('UTC')
    tz_choice = pytz.timezone("Europe/Amsterdam")
    times_ams = {}
    for k, v in times_local.items():
        if v:
            time_str = '%s %s' % (v['date'], v['time'])
            time_ams = tz_local.localize(
                datetime.strptime(
                    time_str, '%Y-%m-%d %H:%M:%SZ')).astimezone(tz_choice)
            times_ams[time_ams] = k

    return times_ams


async def setup(client: Eindjeboss):
    await client.add_cog(F1(client))
