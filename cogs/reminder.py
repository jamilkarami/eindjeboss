import discord
import logging as lg
import uuid
import time
import asyncio
import dateparser
import datetime
import os
from discord.ext import commands
from discord import app_commands
from table2ascii import table2ascii as t2a, PresetStyle
from util.util import get_file, load_json_file, save_json_file
from util.vars.eind_vars import REMINDER_FILE

REMINDER_CHANNEL_ID = int(os.getenv("REMINDER_CHANNEL_ID"))
DATE_PARSER_SETTINGS_AMS = {'PREFER_DATES_FROM': 'future',
                            'DATE_ORDER': 'DMY',
                            'TIMEZONE': 'Europe/Amsterdam',
                            'RETURN_AS_TIMEZONE_AWARE': True}

reminder_file = get_file(REMINDER_FILE)


class Reminder(commands.Cog):
    loop = asyncio.get_running_loop()

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")
        lg.info(f"[{__name__}] Loading reminders")
        await self.startup_reminders()

    @app_commands.command(name="remindme", description="Set a reminder.")
    @app_commands.rename(r_time="reminder-time", msg="message")
    async def remindme(self, intr: discord.Interaction,
                       r_time: str, msg: str, daily: bool):
        parsed_time = dateparser.parse(
            r_time, settings=DATE_PARSER_SETTINGS_AMS)
        r_d = parsed_time.strftime('%A %d/%m/%Y at %H:%M')
        r_t = parsed_time.strftime('%H:%M')
        r_ts = parsed_time.timestamp()

        if not parsed_time:
            await intr.response.send_message(
                "Could not parse the time. Please try again!")
            return

        if not daily:
            if r_ts < time.time():
                await intr.response.send_message(
                    "Stop living in the past, child. Look to the future.")
                return

            await intr.response.send_message(
                f"I will remind you of **{msg}** on **{r_d}** :timer:")
            await self.add_reminder(intr.user, r_ts, msg,
                                    intr.guild_id, daily)

        else:
            await intr.response.send_message(
                f"I will remind you of **{msg}** daily at **{r_t}** :timer:")
            await self.add_reminder(intr.user, r_t, msg,
                                    intr.guild_id, daily)

    @app_commands.command(name="myreminders",
                          description="Get a list of your active reminders.")
    async def myreminders(self, intr: discord.Interaction):
        reminders = load_json_file(reminder_file)
        user_reminders = self.get_user_reminders(intr.user)

        if not user_reminders:
            await intr.response.send_message(
                content="You have no reminders set. Set one with /remindme.",
                ephemeral=True)
            return

        body = []

        for rem in user_reminders:
            if reminders[rem]['repeat']:
                rem_time = reminders[rem]['time']
            else:
                rem_timestamp = datetime.datetime.fromtimestamp(
                    reminders[rem]['time'])
                rem_time = rem_timestamp.strftime("%a %d-%m-%Y - %H:%M")
            reason = reminders[rem]['reason']

            body.append([rem, rem_time, reason])

        output = t2a(
            header=["ID", "Time", "Reason"],
            body=body,
            style=PresetStyle.thin_thick_rounded
        )

        await intr.response.send_message(content=f"```{output}```",
                                         ephemeral=True)

    @app_commands.command(name="deletereminder",
                          description="Delete one of your set reminders.")
    async def deletereminder(self, intr: discord.Interaction, id: str):
        user_reminders = self.get_user_reminders(intr.user)

        for reminder, val in user_reminders.items():
            if reminder == id:
                await self.delete_reminder(id)
                await intr.response.send_message(
                    f"Reminder {id} deleted. ✅", ephemeral=True)
                return

        await intr.response.send_message("ID not found. Please check again.",
                                         ephemeral=True)

    async def startup_reminders(self):
        reminders = load_json_file(reminder_file)

        to_remove = []

        for reminder, vals in reminders.items():
            if not vals['repeat'] and vals['time'] < time.time():
                to_remove.append(reminder)
            else:
                self.loop.create_task(self.start_reminder(
                    reminder,
                    vals['author'],
                    vals['time'],
                    vals['reason'],
                    vals['guild'],
                    vals['repeat']))

        for id in to_remove:
            reminders.pop(id)

        lg.info(
            f"[{__name__}] {len(reminders)} reminders found.")
        save_json_file(reminders, reminder_file)

    async def add_reminder(self, author, time, reason, guild, repeat):
        rem_id = str(uuid.uuid1())[:5]
        reminders = load_json_file(reminder_file)
        reminders[rem_id] = {'author': author.id,
                             'time': time,
                             'reason': reason,
                             'guild': guild,
                             'repeat': repeat}
        save_json_file(reminders, reminder_file)
        await self.start_reminder(rem_id, author.id, time,
                                  reason, guild, repeat)

    async def delete_reminder(self, id):
        reminders = load_json_file(reminder_file)
        del (reminders[id])
        save_json_file(reminders, reminder_file)

    async def start_reminder(self, rem_id, author, tm, reason, g_id, repeat):
        if repeat:
            tm_to_remind = dateparser.parse(
                tm, settings=DATE_PARSER_SETTINGS_AMS).timestamp()
            if tm_to_remind < time.time():
                tm_to_remind = tm_to_remind + 86400
        else:
            tm_to_remind = tm
        user = self.client.get_user(author)

        await asyncio.sleep(tm_to_remind - time.time())
        if rem_id in load_json_file(reminder_file):
            guild = self.client.get_guild(g_id)
            if not repeat or user is None or guild.get_member(user.id) is None:
                await self.delete_reminder(rem_id)
            else:
                self.loop.create_task(self.start_reminder(
                    rem_id, author, tm, reason, g_id, repeat))
            await self.notify_user(reason, user, guild)

    async def notify_user(self, msg, u: discord.user.User, g: discord.Guild):
        channels = await g.fetch_channels()
        reminder_channel = None

        for channel in channels:
            if channel.id == int(REMINDER_CHANNEL_ID):
                reminder_channel = channel

        message = "%s You asked to be reminded of **%s**. It is time! :timer:"
        await reminder_channel.send(message % (u.mention, msg))

    def get_user_reminders(self, user):
        reminders = load_json_file(reminder_file)
        user_reminders = {k: v for k,
                          v in reminders.items() if v['author'] == user.id}
        return user_reminders


async def setup(bot):
    await bot.add_cog(Reminder(bot))
