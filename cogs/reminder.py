import discord
import logging
import uuid
import time
import asyncio
import dateparser
import datetime
import os
from discord.ext import commands
from discord import app_commands
from table2ascii import table2ascii as t2a, PresetStyle
from util.util import *
from util.vars.eind_vars import REMINDER_FILE

REMINDER_CHANNEL_ID = int(os.getenv("REMINDER_CHANNEL_ID"))
DATE_PARSER_SETTINGS = {'PREFER_DATES_FROM': 'future',
                        'DATE_ORDER': 'DMY'}
DATE_PARSER_SETTINGS_AMS = {'PREFER_DATES_FROM': 'future',
                        'DATE_ORDER': 'DMY', 'TIMEZONE': 'Europe/Amsterdam'}

reminder_file = get_file(REMINDER_FILE)


class Reminder(commands.Cog):
    loop = asyncio.get_running_loop()

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"[{__name__}] Cog is ready")
        logging.info(f"[{__name__}] Loading reminders")
        await self.startup_reminders()

    @app_commands.command(name="remindme", description="Set a reminder.")
    async def remindme(self, interaction: discord.Interaction, reminder_time: str, message: str, repeat: bool):
        parsed_time = dateparser.parse(
            reminder_time, settings=DATE_PARSER_SETTINGS_AMS)
        reminder_time_readable_day = parsed_time.strftime('%d/%m/%Y')
        reminder_time_readable_time = parsed_time.strftime('%H:%M')
        reminder_time_timestamp = parsed_time.timestamp()

        if not parsed_time:
            await interaction.response.send_message("Could not parse the time. Please try again!")
            return

        if not repeat:
            if parsed_time.timestamp() < time.time():
                await interaction.response.send_message("Stop living in the past, child. Look to the future.")
                return

            await interaction.response.send_message(
                f"I will remind you of **{message}** on **{reminder_time_readable_day}** at **{reminder_time_readable_time}** :timer:")
            await self.add_reminder(interaction.user, reminder_time_timestamp, message, interaction.guild_id, repeat)

        else:
            await interaction.response.send_message(
                f"I will remind you of **{message}** every day at **{reminder_time_readable_time}** :timer:")
            await self.add_reminder(interaction.user, reminder_time_readable_time, message, interaction.guild_id, repeat)

    @app_commands.command(name="myreminders", description="Get a list of your active reminders.")
    async def myreminders(self, interaction: discord.Interaction):
        reminders = load_json_file(reminder_file)
        user_reminders = self.get_user_reminders(interaction.user)

        if not user_reminders:
            await interaction.response.send_message(
                content="You don't have any reminders set. Set some with /remindme.", ephemeral=True)
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

        await interaction.response.send_message(content=f"```{output}```", ephemeral=True)

    @app_commands.command(name="deletereminder", description="Delete one of your set reminders.")
    async def deletereminder(self, interaction: discord.Interaction, reminder_id: str):
        user_reminders = self.get_user_reminders(interaction.user)

        for reminder, val in user_reminders.items():
            if reminder == reminder_id:
                await self.delete_reminder(reminder_id)
                await interaction.response.send_message(f"Reminder {reminder_id} deleted. ✅", ephemeral=True)
                return

        await interaction.response.send_message(
            "You have no reminders with that ID. Please use /myreminders to check your current reminder IDs.",
            ephemeral=True)

    async def startup_reminders(self):
        reminders = load_json_file(reminder_file)

        to_remove = []
        repeat_count = 0

        for reminder, vals in reminders.items():
            if not vals['repeat'] and vals['time'] < time.time():
                to_remove.append(reminder)
            else:
                if vals['repeat']:
                    repeat_count = repeat_count + 1
                self.loop.create_task(self.start_reminder(
                    reminder, vals['author'], vals['time'], vals['reason'], vals['guild'], vals['repeat']))

        for id in to_remove:
            reminders.pop(id)

        logging.info(
            f"[{__name__}] {len(reminders)} reminders found. ({repeat_count} daily)")
        save_json_file(reminders, reminder_file)

    async def add_reminder(self, author, time, reason, guild, repeat):
        rem_id = str(uuid.uuid1())[:5]
        reminders = load_json_file(reminder_file)
        reminders[rem_id] = {'author': author.id,
                             'time': time, 'reason': reason, 'guild': guild, 'repeat': repeat}
        save_json_file(reminders, reminder_file)
        await self.start_reminder(rem_id, author.id, time, reason, guild, repeat)

    async def delete_reminder(self, id):
        reminders = load_json_file(reminder_file)
        del (reminders[id])
        save_json_file(reminders, reminder_file)

    async def start_reminder(self, reminder_id, author, tm, reason, guild_id, repeat):
        if repeat:
            tm_to_remind = dateparser.parse(
                tm, settings=DATE_PARSER_SETTINGS).timestamp()
            if tm_to_remind < time.time():
                tm_to_remind = tm_to_remind + 86400
        else:
            tm_to_remind = tm
        user = self.client.get_user(author)

        await asyncio.sleep(tm_to_remind - time.time())
        if reminder_id in load_json_file(reminder_file):
            guild = self.client.get_guild(guild_id)
            await self.notify_user(reason, user, guild)
            if not repeat:
                await self.delete_reminder(reminder_id)
            else:
                self.loop.create_task(self.start_reminder(
                    reminder_id, author, tm, reason, guild_id, repeat))

    async def notify_user(self, reason, user: discord.user.User, guild: discord.Guild):
        channels = await guild.fetch_channels()
        reminder_channel = None

        for channel in channels:
            if channel.id == int(REMINDER_CHANNEL_ID):
                reminder_channel = channel

        message = f"{user.mention} You asked to be reminded of **{reason}**. The time has come! :timer:"
        await reminder_channel.send(message)

    def get_user_reminders(self, user):
        reminders = load_json_file(reminder_file)
        user_reminders = {k: v for k,
                          v in reminders.items() if v['author'] == user.id}
        return user_reminders


async def setup(bot):
    await bot.add_cog(Reminder(bot))
