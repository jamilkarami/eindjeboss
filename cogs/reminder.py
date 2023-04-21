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
        self.client: discord.Client = client

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")
        lg.info(f"[{__name__}] Loading reminders")
        await self.startup_reminders()

    @app_commands.command(name="remindme", description="Set a reminder.")
    @app_commands.rename(r_time="reminder-time", msg="message")
    async def remindme(self, intr: discord.Interaction,
                       r_time: str, msg: str, daily: bool):
        rem_id = str(uuid.uuid1())[:5]
        await intr.response.defer()
        parsed_time = dateparser.parse(
            r_time, settings=DATE_PARSER_SETTINGS_AMS)
        r_d = parsed_time.strftime('%A %d/%m/%Y at %H:%M')
        r_t = parsed_time.strftime('%H:%M')
        r_ts = parsed_time.timestamp()

        if not parsed_time:
            await intr.followup.send(
                "Could not parse the time. Please try again!",
                ephemeral=True)
            return

        if r_ts < time.time():
            await intr.followup.send(
                "Stop living in the past, child. Look to the future.",
                ephemeral=True)
            return

        if not daily:
            reminder = mk_reminder(r_ts, msg, intr.guild_id,
                                   daily, intr.user.id)
            self.loop.create_task(self.add_rem(rem_id, reminder))
            await intr.followup.send(
                f"I will remind you of **{msg}** on **{r_d}** :timer:",
                view=ReminderView(rem_id, reminder))

        else:
            reminder = mk_reminder(r_t, msg, intr.guild_id,
                                   daily, intr.user.id)
            self.loop.create_task(self.add_rem(rem_id, reminder))
            await intr.followup.send(
                f"I will remind you of **{msg}** daily at **{r_t}** :timer:")

    @app_commands.command(name="myreminders",
                          description="Get a list of your active reminders.")
    async def myreminders(self, intr: discord.Interaction):
        reminders = get_reminders()
        user_reminders = get_user_reminders(intr.user.id)

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
        rem = get_reminder(id)

        if rem:
            users = rem['users']
            if intr.user.id in users:
                users.remove(intr.user.id)
                if not users:
                    delete_reminder(id)
                else:
                    rem['users'] = users
                    save_reminder(id, rem)
                await intr.response.send_message("Done. ✅", ephemeral=True)
                return

        await intr.response.send_message("Invalid ID. Please check again.",
                                         ephemeral=True)

    async def startup_reminders(self):
        reminders = get_reminders()

        to_remove = []

        for reminder, vals in reminders.items():
            if not vals['repeat'] and vals['time'] < time.time():
                to_remove.append(reminder)
            else:
                self.loop.create_task(self.start_reminder(
                    reminder))

        for id in to_remove:
            reminders.pop(id)

        lg.info(
            f"[{__name__}] {len(reminders)} reminders found.")
        save_reminders(reminders)

    async def add_rem(self, rem_id, reminder):
        reminders = get_reminders()
        reminders[rem_id] = reminder
        save_reminders(reminders)
        await self.start_reminder(rem_id)

    async def start_reminder(self, rem_id):
        rem = get_reminder(rem_id)
        tm = rem['time']
        repeat = rem['repeat']

        if repeat:
            tm_to_remind = dateparser.parse(
                tm, settings=DATE_PARSER_SETTINGS_AMS).timestamp()
            if tm_to_remind < time.time():
                tm_to_remind = tm_to_remind + 86400
        else:
            tm_to_remind = tm

        await asyncio.sleep(tm_to_remind - time.time())

        await self.notify_users(rem_id)
        if not repeat:
            delete_reminder(rem_id)
        else:
            self.start_reminder(rem_id)

    async def notify_users(self, rem_id):
        rem = get_reminder(rem_id)
        guild = await self.client.fetch_guild(rem['guild'])
        reminder_channel = await guild.fetch_channel(REMINDER_CHANNEL_ID)

        users = [await guild.fetch_member(user_id) for user_id in rem['users']]
        msg = rem['reason']

        resp = "%s\nYou asked to be reminded of **%s**. It is time! :timer:"
        resp = resp % (' '.join([u.mention for u in users]), msg)
        await reminder_channel.send(resp)


class ReminderView(discord.ui.View):

    def __init__(self, rem_id, reminder):
        super().__init__()
        self.rem_id = rem_id
        self.reminder = reminder

    @discord.ui.button(label="Remind me too",
                       style=discord.ButtonStyle.blurple)
    async def handle_add_user_reminder(self,
                                       interaction: discord.Interaction,
                                       btn: discord.ui.Button):
        add_user_to_reminder(interaction.user.id, self.rem_id, self.reminder)
        await interaction.response.send_message("Done. ✅", ephemeral=True)


def add_user_to_reminder(user_id, reminder_id, rem):
    reminder = get_reminder(reminder_id)
    if not reminder:
        reminder = rem
    users = reminder.get('users')
    if user_id not in users:
        users.append(user_id)
    reminder['users'] = users
    save_reminder(reminder_id, reminder)


def get_user_reminders(user):
    reminders = get_reminders()
    user_reminders = {k: v for k, v
                      in reminders.items() if user in v['users']}
    return user_reminders


def get_reminders():
    return load_json_file(reminder_file)


def get_reminder(id):
    return get_reminders().get(id)


def mk_reminder(timestamp, msg, guild_id, daily, user):
    return {
        'time': timestamp,
        'reason': msg,
        'guild': guild_id,
        'repeat': daily,
        'users': [user]
    }


def save_reminders(reminders):
    save_json_file(reminders, reminder_file)


def save_reminder(id, reminder):
    reminders = get_reminders()
    reminders[id] = reminder
    save_reminders(reminders)


def delete_reminder(id):
    reminders = get_reminders()
    del (reminders[id])
    save_reminders(reminders)


async def setup(bot):
    await bot.add_cog(Reminder(bot))
