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

REMINDER_FILE = "reminders"

class Reminder(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{__name__} Cog is ready")
        logging.info("Loading reminders")
        await self.startup_reminders()

    @app_commands.command(name="rm", description="Set a reminder")
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

        await interaction.response.send_message(f"I will remind you of {message} on {reminder_time_readable_day} at {reminder_time_readable_time} :timer:")
        await self.add_reminder(interaction.user, reminder_time_timestamp, message)
        return

    @app_commands.command(name="mr", description="Get a list of your active reminders")
    async def myreminders(self, interaction: discord.Interaction):
        reminders = self.load_reminders()
        user_reminders = [reminder for reminder in reminders if reminders[reminder]['author'] == interaction.user.id]

        message_title = f"\n**Reminders for {interaction.user.name}:**\n"

        message = ""
        for rem in user_reminders:
            rem_timestamp = datetime.datetime.fromtimestamp(reminders[rem]['time'])
            rem_time = rem_timestamp.strftime( "%a %d-%m-%Y - %H:%M")  
            reason = reminders[rem]['reason']

            message = message + f"{rem_time} | {reason} | {rem}\n"

        embed = discord.Embed(title=message_title, description=message)
        await interaction.user.send(embed=embed)
        await interaction.response.send_message("✅")
        return

    async def startup_reminders(self):
        reminders = self.load_reminders()

        to_remove = []

        for reminder, vals in reminders.items():
            if vals['time'] < time.time():
                to_remove.append(reminder)
            else:
                await self.start_reminder(reminder, vals['author'], vals['time'], vals['reason'])
        
        for id in to_remove:
            reminders.pop(id)

        self.save_reminders(reminders)

    async def add_reminder(self, author, time, reason):
        rem_id = str(uuid.uuid1())[:5]
        reminders = self.load_reminders()
        reminders[rem_id] = {'author': author.id, 'time': time, 'reason': reason}
        self.save_reminders(reminders)
        await self.start_reminder(rem_id, author.id, time, reason)

    async def delete_reminder(self, id):
        reminders = self.load_reminders()
        del(reminders[id])
        self.save_reminders(reminders)

    def parse_reminders():
        pass

    async def start_reminder(self, reminder_id, author, tm, reason):
        user = self.client.get_user(author)
        logging.info(f"Reminder found for {user.name} for {reason} at {tm}" )
        await asyncio.sleep(tm - time.time())
        if reminder_id in self.load_reminders():
            await user.send(f"You asked to be reminded of **{reason}**. The time has come! :timer:")
            await self.delete_reminder(reminder_id)
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
    

async def setup(bot):
    await bot.add_cog(Reminder(bot))