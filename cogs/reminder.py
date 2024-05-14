import asyncio
import datetime
import logging as lg
import time
import uuid

import dateparser
import discord
from aiocron import crontab
from discord import app_commands
from discord.ext import commands
from table2ascii import PresetStyle
from table2ascii import table2ascii as t2a

from bot import Eindjeboss

SECONDS_IN_DAY = 86400

class Reminder(commands.Cog):
    loop = asyncio.get_running_loop()

    def __init__(self, bot: Eindjeboss):
        self.bot = bot
        self.reminders = self.bot.dbmanager.get_collection("reminders")

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

        tz = await self.bot.get_setting("timezone")
        date_parser_settings = {"PREFER_DATES_FROM": "future", "DATE_ORDER": "DMY", "TIMEZONE": tz,
                                "RETURN_AS_TIMEZONE_AWARE": True}

        tm = dateparser.parse(r_time, settings=date_parser_settings)

        if not tm:
            await intr.followup.send("Could not parse the time. Please try again!", ephemeral=True)
            lg.info("Failed to parse time %s for %s", r_time, intr.user.name)
            return

        p_day = tm.strftime("%A %d/%m/%Y at %H:%M")
        p_time = tm.strftime("%H:%M")
        p_ts = tm.timestamp()

        if p_ts < time.time():
            await intr.followup.send("Stop living in the past, child. Look to the future.", ephemeral=True)
            return

        rem_time = p_time if daily else p_ts

        if daily:
            r = f"I will remind you of **{msg}** daily at **{p_time}** :timer:"
        else:
            r = f"I will remind you of **{msg}** on **{p_day}** :timer:"

        view = ReminderView(rem_id, self)
        rem_msg = await intr.followup.send(r, view=view, wait=True)

        reminder = mk_reminder(rem_id, rem_time, msg, intr.guild_id, daily,
                               intr.user.id, rem_msg.id)

        await self.save_reminder(reminder)

    @app_commands.command(name="myreminders", description="Get a list of your active reminders.")
    async def myreminders(self, intr: discord.Interaction):
        user_reminders = await self.get_user_reminders(intr.user.id)

        if not user_reminders:
            await intr.response.send_message(content="You have no reminders set. Set one with /remindme.",
                                             ephemeral=True)
            return

        body = []

        for rem in user_reminders:
            if rem["daily"]:
                rem_time = rem["time"]
            else:
                rem_timestamp = datetime.datetime.fromtimestamp(rem["time"])
                rem_time = rem_timestamp.strftime("%a %d-%m-%Y - %H:%M")

            msg = rem["msg"]

            body.append([rem["_id"], rem_time, msg])

        output = t2a(
            header=["ID", "Time", "Message"],
            body=body,
            style=PresetStyle.thin_thick_rounded
        )

        await intr.response.send_message(content=f"```{output}```", ephemeral=True)
        lg.info("Sent reminders to %s", intr.user.name)

    @app_commands.command(name="deletereminder",
                          description="Don't get notified for a reminder.")
    @app_commands.rename(rem_id="reminder")
    async def deletereminder(self, intr: discord.Interaction, rem_id: str):
        removed = await self.remove_user_from_reminder(rem_id, intr.user.id)
        if removed:
            await intr.response.send_message("You will not be notified for this reminder.", ephemeral=True)
            return
        await intr.response.send_message("This reminder doesn't exist or you weren't subscribed to it.", ephemeral=True)

    @deletereminder.autocomplete("rem_id")
    async def delete_reminder_autocomplete(self, intr: discord.Interaction,
                                           current: str):
        user_reminders = await self.get_user_reminders(intr.user.id)

        return [
            app_commands.Choice(name=rem["msg"], value=rem["_id"])
            for rem in user_reminders if current.lower() in rem["msg"].lower()
        ]

    # helper functions
    async def startup_reminders(self):
        rems = await self.reminders.find().to_list(length=88675309)

        for reminder in rems:
            if not reminder["daily"] and reminder["time"] < time.time():
                await self.delete_reminder(reminder["_id"])
                continue
            self.loop.create_task(self.start_reminder(reminder))
            if reminder.get("message_id") and reminder["time"] < time.time():
                self.bot.add_view(ReminderView(reminder["_id"], self),
                                  message_id=reminder["message_id"])

    async def add_user_to_reminder(self, rem_id, user_id):
        update = await self.reminders.update_one({"_id": rem_id}, {"$addToSet": {"users": user_id}})
        return update.modified_count

    async def remove_user_from_reminder(self, rem_id, user_id):
        update = await self.reminders.update_one(
            {"_id": rem_id}, {"$pull": {"users": user_id}})
        return update.modified_count

    async def save_reminder(self, reminder):
        await self.reminders.insert_one(reminder)
        self.loop.create_task(self.start_reminder(reminder))

    async def get_reminder(self, rem_id):
        return await self.reminders.find_one({"_id": rem_id})

    async def get_user_reminders(self, user_id):
        return await self.reminders.find({"users": user_id}).to_list(
            length=88675309)

    async def start_reminder(self, reminder):
        rem_id = reminder.get("_id")
        tm = reminder.get("time")
        daily = reminder.get("daily")

        if daily:
            hour, minute = tm.split(":")
            cron_time = f"{minute} {hour} * * *"
            crontab(cron_time, self.notify_users, args=(rem_id,), start=True)
        else:
            if tm >= time.time():
                await asyncio.sleep(tm - time.time())
                await self.notify_users(rem_id)
            await self.delete_reminder(rem_id)

    async def notify_users(self, rem_id):
        rem = await self.reminders.find_one({"_id": rem_id})
        if not rem or not rem["users"]:
            return
        guild = await self.bot.fetch_guild(rem["guild"])
        reminder_channel_id = await self.bot.get_setting("reminder_channel_id")
        reminder_channel = await guild.fetch_channel(reminder_channel_id)

        users = [await guild.fetch_member(user_id) for user_id in rem["users"]]
        msg = rem["msg"]

        resp = "%s\nYou asked to be reminded of **%s**. It is time! :timer:"
        resp = resp % (" ".join([u.mention for u in users]), msg)
        await reminder_channel.send(resp)

    async def delete_reminder(self, rem_id):
        await self.reminders.delete_one({"_id": rem_id})


class ReminderView(discord.ui.View):

    def __init__(self, rem_id, rem_cls):
        super().__init__(timeout=None)
        self.add_item(ReminderButton("Remind me too", rem_id, rem_cls))


class ReminderButton(discord.ui.Button):

    def __init__(self, label, rem_id, rem_cls: Reminder):
        super().__init__()
        self.label = label
        self.r_id = rem_id
        self.rem_cls = rem_cls
        self.custom_id = rem_id
        self.style = discord.ButtonStyle.blurple

    async def callback(self, intr: discord.Interaction):
        add = await self.rem_cls.add_user_to_reminder(self.r_id, intr.user.id)
        if add:
            await intr.response.send_message("Done. ✅", ephemeral=True)
            return
        await intr.response.send_message("You are already subscribed to this reminder.", ephemeral=True)


def mk_reminder(rem_id, timestamp, msg, guild_id, daily, user, msg_id):
    return {
        "_id": rem_id,
        "time": timestamp,
        "msg": msg,
        "guild": guild_id,
        "daily": daily,
        "message_id": msg_id,
        "users": [user]
    }


async def setup(client: Eindjeboss):
    await client.add_cog(Reminder(client))
