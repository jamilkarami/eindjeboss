import logging
from datetime import datetime
from typing import Dict, List

import discord
import pytz
import requests
from discord import app_commands
from discord.ext import commands

from bot import Eindjeboss

event_keys = {
    "FirstPractice": "Practice 1",
    "SecondPractice": "Practice 2",
    "ThirdPractice": "Practice 3",
    "Sprint": "Sprint",
    "SprintQualifying": "Sprint Qualifying",
    "Qualifying": "Qualifying",
    "Race": "Race",
}


def fetch_data(endpoint: str) -> Dict:
    response = requests.get(endpoint)
    response.raise_for_status()
    return response.json()


def get_races(api_url: str) -> List[Dict]:
    year = datetime.today().year
    url = f"{api_url}/{year}.json"
    return fetch_data(url)["MRData"]["RaceTable"]["Races"]


def get_current_round(api_url: str) -> int:
    year = datetime.today().year
    url = f"{api_url}/{year}/next.json"
    data = fetch_data(url)
    return int(data["MRData"]["RaceTable"]["Races"][0]["round"])


def get_times(race_data: Dict) -> Dict:
    times_local = {
        value: race_data.get(
            key, {"date": race_data["date"], "time": race_data["time"]}
        )
        for key, value in event_keys.items()
    }
    return convert_times_to_tz(times_local)


def convert_times_to_tz(times_local: Dict) -> Dict:
    tz_utc = pytz.utc
    tz_ams = pytz.timezone("Europe/Amsterdam")
    times_converted = {}

    for event, timing in times_local.items():
        date_str = timing.get("date")
        time_str = timing.get("time")

        if date_str:
            if time_str:
                dt_utc = tz_utc.localize(
                    datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%SZ")
                )
                event_time = dt_utc.astimezone(tz_ams).strftime("%d/%m at %H:%M")
            else:
                event_time = f"{datetime.strptime(date_str, '%Y-%m-%d').strftime('%d/%m')} at TBA"

            times_converted[event_time] = event

    return dict(sorted(times_converted.items()))


class F1(commands.Cog):
    api_url: str

    def __init__(self, bot: Eindjeboss):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"[{__name__}] Cog is ready")
        self.api_url = await self.bot.get_setting("f1apiurl")

    @app_commands.command(name="nextf1race")
    async def nextf1race(self, interaction: discord.Interaction):
        current_round = get_current_round(self.api_url) - 1
        races = get_races(self.api_url)
        embed = F1Embed(races[current_round], is_current=True)
        await interaction.response.send_message(
            embed=embed, view=F1View(races, current_round)
        )

    def get_current_round(self):
        return get_current_round(self.api_url)


class F1View(discord.ui.View):
    def __init__(self, races: List[Dict], idx: int):
        super().__init__(timeout=300.0)
        self.races = races
        self.current_round = idx
        self.idx = idx
        self.add_item(MoveButton(discord.ButtonStyle.red, "Prev", -1))
        self.add_item(MoveButton(discord.ButtonStyle.green, "Next", 1))

    def get_race_at_idx(self) -> Dict:
        return self.races[self.idx]

    def update_idx(self, update: int):
        self.idx = (self.idx + update) % len(self.races)

    async def update_msg(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=F1Embed(
                self.get_race_at_idx(), is_current=(self.idx == self.current_round)
            )
        )


class F1Embed(discord.Embed):
    def __init__(self, race: Dict, is_current: bool = False):
        color = discord.Color.green() if is_current else discord.Color.red()
        super().__init__(
            color=color, title=f"{race['raceName']} ({datetime.now().year})"
        )
        details = get_times(race)
        for event_time, event_name in details.items():
            self.add_field(name=event_name, value=event_time, inline=False)


class MoveButton(discord.ui.Button):
    def __init__(self, style: discord.ButtonStyle, label: str, update: int):
        super().__init__(style=style, label=label)
        self.update = update

    async def callback(self, interaction: discord.Interaction):
        self.view.update_idx(self.update)
        await self.view.update_msg(interaction)


async def setup(client: Eindjeboss):
    await client.add_cog(F1(client))
