import asyncio
import dateparser
import datetime
import discord
import logging as lg
import os
import time
import uuid
from aiocron import crontab
from discord.ext import commands
from discord import app_commands
from table2ascii import table2ascii as t2a, PresetStyle

REMINDER_CHANNEL_ID = int(os.getenv("REMINDER_CHANNEL_ID"))
DATE_PARSER_SETTINGS_AMS = {'PREFER_DATES_FROM': 'future',
                            'DATE_ORDER': 'DMY',
                            'TIMEZONE': 'Europe/Amsterdam',
                            'RETURN_AS_TIMEZONE_AWARE': True}


class Reminder(commands.Cog):
    loop = asyncio.get_running_loop()

    def __init__(self, client: discord.Client):
        self.client = client
        self.reminders = self.client.dbmanager.get_collection('reminders')

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

        tm = dateparser.parse(r_time, settings=DATE_PARSER_SETTINGS_AMS)

        if not tm:
            await intr.followup.send(
                "Could not parse the time. Please try again!", ephemeral=True)
            lg.info("Failed to parse time %s for %s", r_time, intr.user.name)
            return

        p_day = tm.strftime('%A %d/%m/%Y at %H:%M')
        p_time = tm.strftime('%H:%M')
        p_ts = tm.timestamp()

        if p_ts < time.time():
            await intr.followup.send(
                'Stop living in the past, child. Look to the future.',
                ephemeral=True)
            return

        rem_time = p_time if daily else p_ts
        reminder = mk_reminder(rem_id, rem_time, msg, intr.guild_id, daily,
                               intr.user.id)
        await self.save_reminder(reminder)

        if daily:
            await intr.followup.send(
                f"I will remind you of **{msg}** daily at **{p_time}** :timer:"
            )
            return
        await intr.followup.send(
            f"I will remind you of **{msg}** on **{p_day}** :timer:",
            view=ReminderView(rem_id, self))

    @app_commands.command(name="myreminders",
                          description="Get a list of your active reminders.")
    async def myreminders(self, intr: discord.Interaction):
        user_reminders = await self.get_user_reminders(intr.user.id)

        if not user_reminders:
            await intr.response.send_message(
                content="You have no reminders set. Set one with /remindme.",
                ephemeral=True)
            return

        body = []

        for rem in user_reminders:
            if rem['daily']:
                rem_time = rem['time']
            else:
                rem_timestamp = datetime.datetime.fromtimestamp(rem['time'])
                rem_time = rem_timestamp.strftime("%a %d-%m-%Y - %H:%M")

            msg = rem['msg']

            body.append([rem['_id'], rem_time, msg])

        output = t2a(
            header=["ID", "Time", "Message"],
            body=body,
            style=PresetStyle.thin_thick_rounded
        )

        await intr.response.send_message(content=f"```{output}```",
                                         ephemeral=True)
        lg.info("Sent reminders to %s", intr.user.name)

    @app_commands.command(name="deletereminder",
                          description="Don't get notified for a reminder.")
    @app_commands.rename(rem_id="reminder-id")
    async def deletereminder(self, intr: discord.Interaction, rem_id: str):
        removed = await self.remove_user_from_reminder(rem_id, intr.user.id)
        if removed:
            await intr.response.send_message(
                "You will not be notified for this reminder.", ephemeral=True)
            return
        await intr.response.send_message(
            "This reminder does not exist or you weren't subscribed to it.",
            ephemeral=True
        )

    # helper functions
    async def startup_reminders(self):
        rems = await self.reminders.find().to_list(length=88675309)

        for reminder in rems:
            if not reminder['daily'] and reminder['time'] < time.time():
                await self.delete_reminder(reminder['_id'])
            self.loop.create_task(self.start_reminder(reminder))

    async def add_user_to_reminder(self, rem_id, user_id):
        rem = await self.get_reminder(rem_id)
        if user_id not in rem['users']:
            rem['users'].append(user_id)
            await self.reminders.update_one({'_id': rem_id}, {'$set': rem})
            return True
        return False

    async def remove_user_from_reminder(self, rem_id, user_id):
        rem = await self.get_reminder(rem_id)
        if user_id in rem['users']:
            rem['users'].remove(user_id)

            if not rem['users']:
                await self.reminders.delete_one({'_id': rem_id})
            else:
                await self.reminders.update_one({'_id': rem_id}, {'$set': rem})
            return True
        return False

    async def save_reminder(self, reminder):
        await self.reminders.insert_one(reminder)
        self.loop.create_task(self.start_reminder(reminder))

    async def get_reminder(self, rem_id):
        return await self.reminders.find_one({'_id': rem_id})

    async def get_user_reminders(self, user_id):
        return await self.reminders.find({'users': user_id}).to_list(
            length=88675309)

    async def start_reminder(self, reminder):
        rem_id = reminder.get('_id')
        tm = reminder.get('time')
        daily = reminder.get('daily')

        if daily:
            hour, minute = tm.split(':')
            cron_time = f"{minute} {hour} * * *"
            crontab(cron_time, self.notify_users, args=(rem_id,), start=True)
        else:
            if tm >= time.time():
                await asyncio.sleep(tm - time.time())
                await self.notify_users(rem_id)
            await self.delete_reminder(rem_id)

    async def notify_users(self, rem_id):
        rem = await self.reminders.find_one({'_id': rem_id})
        if not rem:
            return
        guild = await self.client.fetch_guild(rem['guild'])
        reminder_channel = await guild.fetch_channel(REMINDER_CHANNEL_ID)

        users = [await guild.fetch_member(user_id) for user_id in rem['users']]
        msg = rem['msg']

        resp = "%s\nYou asked to be reminded of **%s**. It is time! :timer:"
        resp = resp % (' '.join([u.mention for u in users]), msg)
        await reminder_channel.send(resp)

    async def delete_reminder(self, rem_id):
        await self.reminders.delete_one({'_id': rem_id})


class ReminderView(discord.ui.View):

    def __init__(self, rem_id, rem_cls: Reminder):
        super().__init__(timeout=None)
        self.r_id = rem_id
        self.r_cls = rem_cls

    @discord.ui.button(label="Remind me too",
                       style=discord.ButtonStyle.blurple)
    async def handle_add_user_reminder(self,
                                       intr: discord.Interaction,
                                       btn: discord.ui.Button):
        added = await self.r_cls.add_user_to_reminder(self.r_id, intr.user.id)
        if added:
            await intr.response.send_message("Done. ✅", ephemeral=True)
            return
        await intr.response.send_message(
            "You are already subscribed to this reminder.", ephemeral=True)


def mk_reminder(rem_id, timestamp, msg, guild_id, daily, user):
    return {
        '_id': rem_id,
        'time': timestamp,
        'msg': msg,
        'guild': guild_id,
        'daily': daily,
        'users': [user]
    }


async def setup(client: commands.Bot):
    await client.add_cog(Reminder(client))
