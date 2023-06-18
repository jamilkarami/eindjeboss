import logging as lg
import os
import time
import uuid
from datetime import datetime as dt
from enum import Enum

import discord
import pytz
from discord import app_commands
from discord.ext import commands
from discord.ui import Modal, TextInput

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
        self.ctx_menu = app_commands.ContextMenu(
            name='Report Message',
            callback=self.report_message,
        )
        self.bot.tree.add_command(self.ctx_menu)
        self.tickets = self.bot.dbmanager.get_collection('tickets')

    async def report_message(self, intr: discord.Interaction,
                             msg: discord.Message):
        await intr.response.send_modal(TicketModal(self.tickets, self.bot,
                                                   msg))
        lg.info("Sent ticket modal to %s for message %s",
                intr.user.display_name, msg.jump_url)

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

    @app_commands.command(name="modmail")
    async def modmail(self, intr: discord.Interaction):
        await intr.response.send_modal(
            TicketModal(self.tickets, self.bot))
        lg.info("Sent ticket modal to %s", intr.user.display_name)

    @app_commands.command(name="opentickets")
    async def opentickets(self, intr: discord.Interaction):
        role_id = await self.bot.get_setting("admin_role_id")

        if not await self.validate(intr, role_id):
            return

        tickets = await self.tickets.find(
            {'status': TicketStatus.OPEN.value}).to_list(length=88675309)

        if not tickets:
            await intr.response.send_message(
                "There are currently no open tickets.", ephemeral=True)
            return

        for rep in tickets:
            rep['sub_time'] = dt.fromtimestamp(rep['sub_time']).strftime(D_FMT)

        headers = ['ID', 'Author', 'Title', 'Submission Time']
        fields = ['_id', 'author', 'title', 'sub_time']

        output = tabulate(headers, tickets, fields)

        msg = f"Open tickets:\n```{output}```"

        await intr.response.send_message(msg, ephemeral=True)
        lg.info("%s checked open tickets", intr.user.name)

    @app_commands.command(name="usertickets")
    async def usertickets(self, intr: discord.Interaction,
                          user: discord.Member):
        role_id = await self.bot.get_setting("admin_role_id")

        if not await self.validate(intr, role_id):
            return

        tickets = await self.tickets.find(
            {'author_id': user.id}).to_list(length=88675309)

        if not tickets:
            await intr.response.send_message(
                "This user has no tickets yet.", ephemeral=True)
            return

        for rep in tickets:
            rep['status'] = TicketStatus(rep['status']).name
            rep['sub_time'] = dt.fromtimestamp(rep['sub_time']).strftime(D_FMT)

        headers = ['ID', 'Title', 'Submission Date', 'Status']
        fields = ['_id', 'title', 'sub_time', 'status']

        output = tabulate(headers, tickets, fields)
        msg = f"Tickets submitted by **{user.display_name}**\n```{output}```"

        await intr.response.send_message(msg, ephemeral=True)
        lg.info("%s checked user tickets from %s", intr.user.name,
                user.name)

    @app_commands.command(name="handleticket")
    @app_commands.rename(ticket_id="ticket-id")
    async def handleticket(self, intr: discord.Interaction, ticket_id: str):
        role_id = await self.bot.get_setting("admin_role_id")

        if not await self.validate(intr, role_id):
            return

        mod_category_id = await self.bot.get_setting("moderator_category_id")
        ticket = await self.tickets.find_one({"_id": ticket_id})

        if not ticket:
            await intr.response.send_message(TICKET_NOT_FOUND, ephemeral=True)
            return

        old_status = ticket['status']

        if TicketStatus.IN_PROGESS.value == old_status:
            channel = await intr.guild.fetch_channel(ticket['channel'])
            resp = f"Ticket already in progress: {channel.mention}"
            await intr.response.send_message(resp, ephemeral=True)
            return

        ticket_title = ticket['title']
        author_id = ticket['author_id']
        description = ticket['description']

        moderation_category = await intr.guild.fetch_channel(mod_category_id)
        user = await intr.guild.fetch_member(author_id)

        mod_role = discord.utils.get(intr.guild.roles, name="Moderator")
        admin_role = discord.utils.get(intr.guild.roles, name="Admin")
        overwrites = make_overwrites(intr.guild, user, [mod_role, admin_role])
        channel_name = f"{user.name}-{ticket_id}"
        rep_channel = await moderation_category.create_text_channel(
            channel_name, overwrites=overwrites)

        await self.tickets.update_one(
            {"_id": ticket_id}, [{"$set":
                                  {"channel": rep_channel.id,
                                   "status": TicketStatus.IN_PROGESS.value,
                                   "updated": int(time.time())}}])

        lg.info("%s started handling ticket %s", intr.user.name, ticket_id)
        msg = f"**Ticket submitted by {user.mention}**\n\n"
        embed = discord.Embed(title=ticket_title, description=description)
        await rep_channel.send(msg, embed=embed)

        if "message_content" in ticket:
            data = ticket["message_content"]
            author = data["message_author"]
            url = data["url"]
            attachments = []

            msg = f"**Reference: {url} sent by {author}:**\n\n"

            if data["content"]:
                msg_content = data["content"]
                msg += f"_\"{msg_content}\"_"
            if data.get("img_paths"):
                for path in data["img_paths"]:
                    attachments.append(discord.File(path))

            await rep_channel.send(msg, files=attachments)

        if TicketStatus.OPEN.value == old_status:
            resp = f"Ticket in progress: {rep_channel.mention}"
            lg.info("Ticket %s in progress by %s", ticket_id, intr.user.id)
        else:
            resp = f"Ticket reopened: {rep_channel.mention}"
            lg.info("Ticket %s reopened by %s", ticket_id, intr.user.id)

        await intr.response.send_message(resp, ephemeral=True)

    @app_commands.command(name="closeticket")
    @app_commands.rename(ticket_id="ticket-id")
    async def closeticket(self, intr: discord.Interaction,
                          ticket_id: str):
        role_id = await self.bot.get_setting("admin_role_id")

        if not await self.validate(intr, role_id):
            return

        ticket = await self.tickets.find_one({"_id": ticket_id})

        if not ticket:
            await intr.response.send_message(TICKET_NOT_FOUND, ephemeral=True)
            return
        if TicketStatus.CLOSED.value == ticket["status"]:
            await intr.response.send_message(ALREADY_CLOSED, ephemeral=True)
            return

        ticket["status"] = TicketStatus.CLOSED.value
        ticket["updated"] = int(time.time())

        if "channel" in ticket:
            channel = await intr.guild.fetch_channel(ticket['channel'])
            await channel.delete()

        await self.tickets.update_one({"_id": ticket_id}, {"$set": ticket})
        await intr.response.send_message(TICKET_CLOSED, ephemeral=True)
        lg.info("Ticket %s closed by %s", ticket_id, intr.user.name)

    @closeticket.autocomplete("ticket_id")
    async def closeticket_autocomplete(self, intr: discord.Interaction,
                                       current: str):
        tickets = await self.tickets.find(
            {"status": {"$ne": 3},
             "title": {"$regex": current}}).to_list(length=88675309)

        return [
            app_commands.Choice(name=ticket["title"], value=ticket["_id"])
            for ticket in tickets
        ]

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


class TicketModal(Modal):

    def __init__(self, collection, bot: Eindjeboss,
                 message: discord.Message = None):
        super().__init__(title="Submit a ticket", timeout=600)
        self.collection = collection
        self.message = message
        self.bot = bot

    ticket_title = TextInput(
        label="Subject", style=discord.TextStyle.short,
        placeholder="Short, descriptive title goes here")

    description = TextInput(label="Description",
                            style=discord.TextStyle.paragraph,
                            placeholder="Tell us what's up",
                            max_length=1024)

    async def on_submit(self, intr: discord.Interaction):
        ticket_channel_id = await self.bot.get_setting(
            "modmail_channel", None)
        ticket_id = str(uuid.uuid1())[:5]

        tick_type = "report" if self.message else "ticket"
        msg = (f"New {tick_type} submitted by {intr.user.display_name}."
               f" Respond to it with /handleticket {ticket_id}")

        embed_author = f"Ticket by {intr.user.display_name}"
        embed_title = self.ticket_title.value
        embed_description = self.description.value

        embed = discord.Embed(title=embed_title,
                              description=embed_description,
                              color=discord.Color.red())

        embed.set_author(name=embed_author)

        data = {'_id': ticket_id,
                'author': intr.user.display_name,
                'author_id': intr.user.id,
                'title': self.ticket_title.value,
                'description': self.description.value,
                'sub_time': int(time.time()),
                'status': TicketStatus.OPEN.value}

        if self.message:
            data['message_id'] = self.message.id
            data['message_content'] = await self.get_msg_data(ticket_id,
                                                              self.message)
            msg_url = f"[Link]({self.message.jump_url})"
            embed.add_field(name="Reference", value=msg_url)

        self.collection.insert_one(data)
        await intr.response.send_message("Ticket submitted.",
                                         ephemeral=True)

        channel = await intr.guild.fetch_channel(ticket_channel_id)
        await channel.send(content=msg, embed=embed)
        lg.info("%s submitted ticket %s", intr.user.name, ticket_id)

    async def on_error(self, intr: discord.Interaction,
                       error: Exception) -> None:
        await intr.response.send_message(
            "There was an error with the ticket. Please try again.",
            ephemeral=True)
        lg.error(error)

    async def on_timeout(self) -> None:
        return

    async def get_msg_data(self, ticket: str, message: discord.Message):
        data = {"url": message.jump_url,
                "message_author": message.author.mention}

        if message.content:
            data['content'] = message.content
        if message.attachments:
            paths = []
            for idx, attachment in enumerate(message.attachments, start=1):
                report_dir = f"{self.bot.file_dir}/reports/{ticket}/"
                path = report_dir + f"{idx}_{attachment.filename}"
                os.makedirs(report_dir, exist_ok=True)
                await attachment.save(path)
                paths.append(path)
            data['img_paths'] = paths

        return data


class TicketStatus(Enum):
    OPEN = 1
    IN_PROGESS = 2
    CLOSED = 3


def make_overwrites(guild: discord.Guild, user: discord.Member, roles):
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(read_messages=True),
    }
    for role in roles:
        overwrites[role] = discord.PermissionOverwrite(read_messages=True)
    return overwrites


async def setup(client: Eindjeboss):
    await client.add_cog(Admin(client))
