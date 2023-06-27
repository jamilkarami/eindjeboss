import logging as lg
import os
import uuid
from datetime import datetime as dt

import discord
import pytz
from discord import app_commands
from discord.ext import commands

from bot import Eindjeboss
from util.util import download_img_from_url, tabulate

TICKET_NOT_FOUND = ("Failed to find a ticket with this ID"
                    " or the channel you're in isn't a ticket channel."
                    " Please double check.")
ALREADY_CLOSED = "This ticket is already closed."
TICKET_CLOSED = "Ticket closed."
D_FMT = "%Y-%m-%d %H:%M"


class Admin(commands.Cog):

    def __init__(self, bot: Eindjeboss):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @commands.command(name="sync")
    async def sync(self, ctx: commands.Context):
        if ctx.author.id != self.bot.owner_id:
            return
        await self.bot.sync_and_update()
        await ctx.message.add_reaction("✅")

    @app_commands.command(name="reloadsettings")
    async def reload_settings(self, intr: discord.Interaction):
        if not await self.validate(intr):
            return
        await intr.response.defer(ephemeral=True)
        await self.bot.load_settings()
        await intr.followup.send("Settings reloaded", ephemeral=True)
        lg.info("Reloaded settings")

    @app_commands.command(name="now")
    async def now(self, intr: discord.Interaction):
        tz = await self.bot.get_setting("timezone")
        resp = dt.now(tz=pytz.timezone(tz))
        await intr.response.send_message(resp, ephemeral=True)
        lg.info("%s used /now")

    @app_commands.command(name="nuke")
    async def nuke(self, intr: discord.Interaction, number: int):
        role_id = await self.bot.get_setting("admin_role_id")

        if not await self.validate(intr, role_id):
            return

        await intr.channel.purge(limit=number)
        await intr.response.send_message("Done", ephemeral=True)
        lg.info("%s purged %s messages in channel %s", intr.user.name, number,
                intr.channel.name)

    @app_commands.command(name='logs')
    @app_commands.describe(full="Choose true if you want the full log file.",
                           ln="The number of log lines to send.")
    async def logs(self, intr: discord.Interaction, ln: int = 20,
                   full: bool = False):
        role_id = await self.bot.get_setting("admin_role_id")

        if not await self.validate(intr, role_id):
            return

        logging_file_name = f"{self.bot.file_dir}/logs/eindjeboss.log"

        if full:
            await intr.user.send(file=discord.File(logging_file_name))
            await intr.response.send_message("Done.", ephemeral=True)
            lg.info("Sent full log file to %s", intr.user.name)
            return

        log_file = open(logging_file_name)
        lines = log_file.readlines()
        log_lines = lines[-min(len(lines), ln):]

        log_msg = ""
        for line in log_lines:
            if len(log_msg) + len(line) > 2000:
                await intr.user.send(f'```{log_msg}```')
                log_msg = ""
            log_msg = log_msg + line
        await intr.user.send(f'```{log_msg}```')
        await intr.response.send_message("Done.", ephemeral=True)
        lg.info("Sent logs to %s", intr.user.name)

    @app_commands.command(name="set")
    @app_commands.rename(name="setting-name", new_vl="new-value")
    async def set(self, intr: discord.Interaction, name: str = None,
                  new_vl: str = None):
        role_id = await self.bot.get_setting("admin_role_id")

        if not await self.validate(intr, role_id):
            return

        if not name:
            settings = await self.bot.get_settings()

            headers = ["ID", "Value", "Description"]
            fields = ["_id", "value", "description"]
            table = tabulate(headers, settings, fields)

            msg = f"Current settings:\n```{table}```"
            await intr.response.send_message(msg, ephemeral=True)
            return

        if not new_vl:
            setting = await self.bot.settings.find_one({"_id": name})
            msg = "%s | %s | %s" % (setting['_id'], setting['value'],
                                    setting['description'])
            await intr.response.send_message(msg, ephemeral=True)
            return

        if new_vl.isdigit():
            new_vl = int(new_vl)

        old_doc = await self.bot.update_setting({"_id": name, "value": new_vl})
        if not old_doc:
            await intr.response.send_message(
                "Could not find setting with name %s" % name, ephemeral=True)
            return

        old_val = old_doc["value"]
        msg = f"Updated setting {name} with value {new_vl} (was {old_val})"
        await intr.response.send_message(msg, ephemeral=True)
        lg.info("%s changed setting %s from %s to %s", intr.user.name, name,
                old_val, new_vl)

    @set.autocomplete("name")
    async def set_autocomplete(self, intr: discord.Interaction, curr: str):
        settings = await self.bot.get_settings()

        return [
            app_commands.Choice(name=setting["_id"], value=setting["_id"])
            for setting in settings if curr.lower() in setting["_id"].lower()
        ]

    @app_commands.command(name="createsetting")
    @app_commands.rename(setting="setting-name", value="initial-value")
    async def createsetting(self, intr: discord.Interaction, setting: str,
                            description: str, value: str):
        if not await self.validate(intr):
            return

        if value.isdigit():
            value = int(value)
        await self.bot.add_setting({"_id": setting,
                                    "description": description,
                                    "value": value})
        msg = f"Created setting **{setting}** with initial value **{value}**"
        await intr.response.send_message(msg, ephemeral=True)
        lg.info("%s created setting %s with value %s", intr.user.name, setting,
                value)

    async def validate(self, intr: discord.Interaction, role_id: int = None):
        if intr.user.id == self.bot.owner_id:
            return True

        if role_id:
            role = intr.guild.get_role(role_id)
            if role in intr.user.roles:
                return True

        await intr.response.send_message(
            "You are not allowed to use this command.", ephemeral=True)
        await self.bot.alert_owner(
            "%s tried to use /%s. Check integration permissions"
            % (intr.user.name, intr.data.get("name")))
        return False

    @app_commands.command(name="copyemoji")
    @app_commands.rename(emoji_str="emoji")
    async def copyemoji(self, intr: discord.Interaction,
                        emoji_str: str, name: str = None):
        await intr.response.defer(ephemeral=True)
        emoji = discord.PartialEmoji.from_str(emoji_str)

        if not emoji.url or not emoji.id:
            await intr.followup.send("Invalid emoji", ephemeral=True)
            return

        try:
            await intr.guild.fetch_emoji(emoji.id)
        except Exception:
            pass
        else:
            await intr.followup.send("This emoji is from this server.",
                                     ephemeral=True)
            return

        if not name:
            name = emoji.name

        img_name = emoji.url.split("/")[-1]
        img_path = f"temp/{uuid.uuid4()}_{img_name}"
        img_file = download_img_from_url(
            emoji.url + "?size=96&quality=lossless", img_path)

        with open(img_file, 'rb') as ef:
            await intr.guild.create_custom_emoji(
                name=name, image=ef.read(), reason="Copied Emoji")
        await intr.followup.send("Done", ephemeral=True)
        lg.info("%s copied an emoji", intr.user.name)
        os.remove(img_file)


async def setup(client: Eindjeboss):
    await client.add_cog(Admin(client))
