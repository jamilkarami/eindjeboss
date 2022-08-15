from code import interact
import discord
from discord.ext import commands
from discord import app_commands
import logging
import pickle
import uuid
import time
import asyncio
import dateparser
import datetime
import os
from table2ascii import table2ascii as t2a, PresetStyle

REMINDER_FILE = "reminders"
REMINDER_CHANNEL_ID = int(os.getenv("REMINDER_CHANNEL_ID"))

class Reminder(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{__name__} Cog is ready")
        logging.info("Loading reminders")
        await self.startup_reminders()

    @app_commands.command(name="remindme", description="Set a reminder")
    async def remindme(self, interaction: discord.Interaction, reminder_time: str, message: str):

        parsed_time = dateparser.parse(reminder_time, settings={'PREFER_DATES_FROM': 'future'})
        
        if parsed_time.timestamp() < time.time():
            await interaction.response.send_message("Stop living in the past, child. Look to the future.")
            return

        if not parsed_time:
            await interaction.response.send_message("Could not parse the time. Please try again!")
            return

        reminder_time_readable_day = parsed_time.strftime('%d/%m/%Y')
        reminder_time_readable_time = parsed_time.strftime('%I:%M %p')
        reminder_time_timestamp = parsed_time.timestamp()

        await interaction.response.send_message(f"I will remind you of **{message}** on **{reminder_time_readable_day}** at **{reminder_time_readable_time}** :timer:")
        await self.add_reminder(interaction.user, reminder_time_timestamp, message, interaction.guild_id)
        return

    @app_commands.command(name="myreminders", description="Get a list of your active reminders")
    async def myreminders(self, interaction: discord.Interaction):
        reminders = self.load_reminders()
        user_reminders = self.get_user_reminders(interaction.user)

        if not user_reminders:
            await interaction.response.send_message(content="You don't have any reminders set. Set some with /remindme.", ephemeral=True)
            return

        body = []

        for rem in user_reminders:
            rem_timestamp = datetime.datetime.fromtimestamp(reminders[rem]['time'])
            rem_time = rem_timestamp.strftime( "%a %d-%m-%Y - %H:%M")  
            reason = reminders[rem]['reason']

            body.append([rem, rem_time, reason])

        output = t2a(
            header=["ID", "Time", "Reason"],
            body=body,
            style=PresetStyle.thin_compact
        )

        await interaction.response.send_message(content=f"```{output}```", ephemeral=True)
        return

    @app_commands.command(name="deletereminder", description="Delete one of your set reminders")
    async def deletereminder(self, interaction: discord.Interaction, reminder_id : str):
        user_reminders = self.get_user_reminders(interaction.user)
        
        for reminder, val in user_reminders.items():
            if reminder == reminder_id:
                await self.delete_reminder(reminder_id)
                await interaction.response.send_message(f"Reminder {reminder_id} deleted. ✅", ephemeral=True)
                return
        
        await interaction.response.send_message("You have no reminders with that ID. Please use /myreminders to check your current reminder IDs.", ephemeral=True)
        return

    async def startup_reminders(self):
        reminders = self.load_reminders()

        to_remove = []
        loop = asyncio.get_running_loop()

        for reminder, vals in reminders.items():
            if vals['time'] < time.time():
                to_remove.append(reminder)
            else:
                loop.create_task(self.start_reminder(reminder, vals['author'], vals['time'], vals['reason'], vals['guild']))
        
        for id in to_remove:
            reminders.pop(id)

        self.save_reminders(reminders)

    async def add_reminder(self, author, time, reason, guild):
        rem_id = str(uuid.uuid1())[:5]
        reminders = self.load_reminders()
        reminders[rem_id] = {'author': author.id, 'time': time, 'reason': reason, 'guild': guild}
        self.save_reminders(reminders)
        await self.start_reminder(rem_id, author.id, time, reason, guild)

    async def delete_reminder(self, id):
        reminders = self.load_reminders()
        del(reminders[id])
        self.save_reminders(reminders)

    def parse_reminders():
        pass

    async def start_reminder(self, reminder_id, author, tm, reason, guild_id):
        user = self.client.get_user(author)

        logging.info(f"Reminder found for {user.name} for {reason} at {tm}" )
        await asyncio.sleep(tm - time.time())
        if reminder_id in self.load_reminders():
            guild = self.client.get_guild(guild_id)
            await self.notify_user(reason, user, guild)
            await self.delete_reminder(reminder_id)
            return

    async def notify_user(self, reason, user : discord.user.User, guild : discord.Guild):
        channels = await guild.fetch_channels()
        reminder_channel = None
        
        for channel in channels:
            if channel.id == int(REMINDER_CHANNEL_ID):
                reminder_channel = channel

        message = f"{user.mention} You asked to be reminded of **{reason}**. The time has come! :timer:"
        await reminder_channel.send(message)
        return

    def load_reminders(self):
        with open(REMINDER_FILE, "rb") as reminder_file:
            try:
                return pickle.load(reminder_file)
            except EOFError:
                return dict()

    def save_reminders(self, reminders):
        with open(REMINDER_FILE, 'wb') as reminder_file:
            pickle.dump(reminders, reminder_file)

    def get_user_reminders(self, user):
        reminders = self.load_reminders()
        user_reminders = {k: v for k,v in reminders.items() if v['author'] == user.id}
        return user_reminders
    

async def setup(bot):
    await bot.add_cog(Reminder(bot))