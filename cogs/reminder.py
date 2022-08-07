from discord.ext import commands
import logging
import pickle
import uuid
import time
import asyncio
import dateparser

REMINDER_FILE = "reminders"

class Reminder(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{__name__} Cog is ready")

    @commands.command(aliases=["rm"])
    async def remindme(self, ctx, *args):

        def check_reply(author):
            def inner_check(message):
                return message.author == author
            return inner_check

        query = " ".join(args)
        reminder_time = dateparser.parse(query)

        if reminder_time.timestamp() < time.time():
            await ctx.message.reply("Stop living in the past, child. Look to the future.")
            return

        if not reminder_time:
            await ctx.message.reply("Could not parse the time. Please try again!")
            return

        reminder_time_readable_day = reminder_time.strftime('%m/%d/%Y')
        reminder_time_readable_time = reminder_time.strftime('%I:%M %p')
        reminder_time_timestamp = reminder_time.timestamp()
        
        await ctx.message.reply("What would you like to be reminded of?")

        reminder_message = await self.client.wait_for("message", check=check_reply(ctx.message.author))

        await reminder_message.reply(f"I will remind you of {reminder_message.content} on {reminder_time_readable_day} at {reminder_time_readable_time} :timer:")
        await self.add_reminder(ctx.message.author, reminder_time_timestamp, reminder_message.content)
        return

    async def startup_reminders(self):
        reminders = self.load_reminders()

        to_remove = []

        for reminder, vals in reminders.items():
            if vals['time'] < time.time():
                to_remove.append(reminder)
            else:
                await self.start_reminder(vals['author'], vals['time'], vals['reason'])
        
        for id in to_remove:
            reminders.pop(id)

        self.save_reminders(reminders)

    async def add_reminder(self, author, time, reason):
        reminders = self.load_reminders()
        reminders[uuid.uuid1()] = {'author': author.id, 'time': time, 'reason': reason}
        self.save_reminders(reminders)
        await self.start_reminder(author.id, time, reason)

    def parse_reminders():
        pass

    async def start_reminder(self, author, tm, reason):
        user = self.client.get_user(author)
        print(f"Will remind {user.name} of {reason} in {tm - time.time()}" )
        await asyncio.sleep(tm - time.time())
        await user.send(f"You asked to be reminded of {reason}. The time has come! :timer:")

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