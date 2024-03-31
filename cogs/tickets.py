import base64
import logging as lg
import os
import time
import uuid
from datetime import datetime as dt
from enum import Enum

import discord
from aiocron import crontab
from discord import app_commands
from discord.ext import commands
from discord.ui import Modal, TextInput

from bot import Eindjeboss
from util.util import tabulate
from util.vars.eind_vars import CHANNEL_IGNORE_LIST
from util.vars.periodics import SYNC_TICKET_DT

TICKET_NOT_FOUND = ("Failed to find a ticket with this ID or the channel you're in isn't a ticket channel."
                    " Please double check.")
ALREADY_CLOSED = "This ticket is already closed."
TICKET_CLOSED = "Ticket closed."
NO_OPEN_TICKETS = "There are currently no open tickets."
USER_HAS_NO_TICKETS = "This user has no tickets yet."
NOT_INSIDE_TICKET_CHANNEL = "You are not inside a ticket channel"
TICKET_HAS_NO_NOTES = "This ticket doesn't have any notes yet."
COMMAND_NOT_ALLOWED = "You are not allowed to use this command."

D_FMT = "%Y-%m-%d %H:%M"


class Ticket(commands.GroupCog):

    def __init__(self, bot: Eindjeboss):
        self.bot = bot
        self.ctx_menu = app_commands.ContextMenu(
            name="Report Message",
            callback=self.report_message,
        )
        self.bot.tree.add_command(self.ctx_menu)
        self.tickets = self.bot.dbmanager.get_collection("tickets")
        self.tracked_tickets = {}

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")
        await self.load_open_ticket_info()
        crontab(SYNC_TICKET_DT, func=self.sync_tickets, start=True)

    async def report_message(self, intr: discord.Interaction, msg: discord.Message):
        await intr.response.send_modal(TicketModal(self.tickets, self.bot, msg))
        lg.info("Sent ticket modal to %s for message %s", intr.user.display_name, msg.jump_url)

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author == self.bot.user:
            return
        if msg.channel.id in CHANNEL_IGNORE_LIST:
            return

        ticket = await self.get_ticket_from_channel_id(msg.channel.id)

        if not ticket:
            return

        msg_data = await self.get_data_from_msg(msg)

        self.tracked_tickets[msg.channel.id][1]["messages"].append(msg_data)
        self.tracked_tickets[msg.channel.id][0] = True

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent):
        msg = payload.cached_message

        if not msg:
            msg_channel = await self.bot.fetch_channel(payload.channel_id)
            msg = await msg_channel.fetch_message(payload.message_id)

        if msg.author == self.bot.user:
            return
        if msg.channel.id in CHANNEL_IGNORE_LIST:
            return

        ticket = await self.get_ticket_from_channel_id(msg.channel.id)

        if not ticket:
            return

        print(ticket["messages"][0])
        old_msg_idx, old_msg = next((idx, o_msg) for idx, o_msg in enumerate(ticket["messages"])
                                    if o_msg["id"] == msg.id)

        if not old_msg_idx:
            return

        edit_history = old_msg.get("edit_history", [])

        edit_history.append({"content": old_msg["content"], "time": old_msg["time"]})
        old_msg["content"] = msg.content
        old_msg["time"] = msg.edited_at
        old_msg["edit_history"] = edit_history

        ticket["messages"][old_msg_idx] = old_msg

        self.tracked_tickets[msg.channel.id] = [True, ticket]

    @app_commands.command(name="modmail")
    async def modmail(self, intr: discord.Interaction):
        await intr.response.send_modal(TicketModal(self.tickets, self.bot))
        lg.info("Sent ticket modal to %s", intr.user.display_name)

    @app_commands.command(name="pending")
    async def opentickets(self, intr: discord.Interaction):
        admin_role_id = await self.bot.get_setting("admin_role_id")
        mod_role_id = await self.bot.get_setting("mod_role_id")

        if not await self.validate(intr, [admin_role_id, mod_role_id]):
            return

        tickets = await self.tickets.find({"status": TicketStatus.OPEN.name}).to_list(length=88675309)

        if not tickets:
            await intr.response.send_message(NO_OPEN_TICKETS, ephemeral=True)
            return

        for rep in tickets:
            rep["sub_time"] = dt.fromtimestamp(rep["sub_time"]).strftime(D_FMT)

        headers = ["ID", "Author", "Title", "Submission Time"]
        fields = ["_id", "author", "title", "sub_time"]

        output = tabulate(headers, tickets, fields)

        msg = f"Open tickets:\n```{output}```"

        await intr.response.send_message(msg, ephemeral=True)
        lg.info("%s checked open tickets", intr.user.name)

    @app_commands.command(name="fromuser")
    async def usertickets(self, intr: discord.Interaction,
                          user: discord.Member):
        admin_role_id = await self.bot.get_setting("admin_role_id")
        mod_role_id = await self.bot.get_setting("mod_role_id")

        if not await self.validate(intr, [admin_role_id, mod_role_id]):
            return

        tickets = await self.tickets.find(
            {"author_id": user.id}).to_list(length=88675309)

        if not tickets:
            await intr.response.send_message(USER_HAS_NO_TICKETS, ephemeral=True)
            return

        for rep in tickets:
            rep["status"] = TicketStatus(rep["status"]).name
            rep["sub_time"] = dt.fromtimestamp(rep["sub_time"]).strftime(D_FMT)

        headers = ["ID", "Title", "Submission Date", "Status"]
        fields = ["_id", "title", "sub_time", "status"]

        output = tabulate(headers, tickets, fields)
        msg = f"Tickets submitted by **{user.display_name}**\n```{output}```"

        await intr.response.send_message(msg, ephemeral=True)
        lg.info("%s checked user tickets from %s", intr.user.name, user.name)

    @app_commands.command(name="handle")
    @app_commands.rename(ticket_id="ticket-id")
    async def handleticket(self, intr: discord.Interaction, ticket_id: str):
        admin_role_id = await self.bot.get_setting("admin_role_id")
        mod_role_id = await self.bot.get_setting("mod_role_id")

        if not await self.validate(intr, [admin_role_id, mod_role_id]):
            return

        mod_category_id = await self.bot.get_setting("moderator_category_id")

        ticket = await self.get_ticket_from_id(ticket_id)

        if not ticket:
            await intr.response.send_message(TICKET_NOT_FOUND, ephemeral=True)
            return

        old_status = ticket["status"]

        if TicketStatus.IN_PROGRESS == TicketStatus[old_status]:
            channel = await intr.guild.fetch_channel(ticket["channel"])
            resp = f"Ticket already in progress: {channel.mention}"
            await intr.response.send_message(resp, ephemeral=True)
            return

        ticket_title = ticket["title"]
        author_id = ticket["author_id"]
        description = ticket["description"]

        moderation_category = await intr.guild.fetch_channel(mod_category_id)
        user = await intr.guild.fetch_member(author_id)

        mod_role = discord.utils.get(intr.guild.roles, id=mod_role_id)
        admin_role = discord.utils.get(intr.guild.roles, id=admin_role_id)
        overwrites = make_overwrites(intr.guild, user, [mod_role, admin_role])
        channel_name = f"{user.name}-{ticket_id}"
        rep_channel = await moderation_category.create_text_channel(
            channel_name, overwrites=overwrites)

        await self.tickets.update_one(
            {"_id": ticket_id}, [{"$set": {"channel": rep_channel.id, "status": TicketStatus.IN_PROGRESS.name,
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

        if TicketStatus.OPEN == TicketStatus[old_status]:
            resp = f"Ticket in progress: {rep_channel.mention}"
            lg.info("Ticket %s in progress by %s", ticket_id, intr.user.id)
        else:
            resp = f"Ticket reopened: {rep_channel.mention}"
            lg.info("Ticket %s reopened by %s", ticket_id, intr.user.id)

        await intr.response.send_message(resp, ephemeral=True)

        d_name = intr.user.display_name
        title = ticket["title"]

        self.tracked_tickets[intr.channel_id] = [True, ticket]
        await self.bot.alert_mods(
            f"**{d_name}** started handling ticket {ticket_id} ({title})")

    @app_commands.command(name="close")
    @app_commands.rename(ticket_id="ticket")
    async def closeticket(self, intr: discord.Interaction,
                          ticket_id: str = None):

        admin_role_id = await self.bot.get_setting("admin_role_id")
        mod_role_id = await self.bot.get_setting("mod_role_id")

        if not await self.validate(intr, [admin_role_id, mod_role_id]):
            return

        if not ticket_id:
            if intr.channel_id not in self.tracked_tickets:
                await intr.response.send_message(NOT_INSIDE_TICKET_CHANNEL, ephemeral=True)
                return
            ticket = await self.get_ticket_from_channel_id(intr.channel_id)
        else:
            ticket = await self.get_ticket_from_id(ticket_id)

        if not ticket:
            await intr.response.send_message(TICKET_NOT_FOUND, ephemeral=True)
            return
        if TicketStatus.CLOSED == TicketStatus[ticket["status"]]:
            await intr.response.send_message(ALREADY_CLOSED, ephemeral=True)
            return

        ticket["status"] = TicketStatus.CLOSED.name
        ticket["updated"] = int(time.time())

        if "channel" in ticket:
            channel = intr.guild.get_channel(ticket["channel"])
            if channel:
                await channel.delete()

        await self.tickets.update_one({"_id": ticket_id}, {"$set": ticket})
        await intr.response.send_message(TICKET_CLOSED, ephemeral=True)
        lg.info("Ticket %s closed by %s", ticket_id, intr.user.name)

        d_name = intr.user.display_name
        title = ticket["title"]
        await self.bot.alert_mods(f"**{d_name}** closed ticket {ticket_id} ({title})")

    @app_commands.command(name="note")
    @app_commands.rename(ticket_id="ticket")
    async def noteticket(self, intr: discord.Interaction, ticket_id: str, text: str = None):
        admin_role_id = await self.bot.get_setting("admin_role_id")
        mod_role_id = await self.bot.get_setting("mod_role_id")

        if not await self.validate(intr, [admin_role_id, mod_role_id]):
            return

        ticket = await self.get_ticket_from_id(ticket_id)
        notes = ticket.get("notes")

        if not text:
            if not notes:
                await intr.response.send_message(TICKET_HAS_NO_NOTES, ephemeral=True)
                return

            headers = ["Added By", "Note", "Time"]
            fields = ["added_by", "text", "time_added"]

            output = tabulate(headers, notes, fields)
            msg = f"Notes for ticket **{ticket_id}**\n```{output}```"

            await intr.response.send_message(msg, ephemeral=True)
            return

        submitter = intr.user.display_name
        submitted_time = dt.fromtimestamp(time.time()).strftime(D_FMT)

        note = {
            "added_by": submitter,
            "text": text,
            "time_added": submitted_time
        }

        if not notes:
            notes = []
        notes.append(note)
        ticket["notes"] = notes

        await self.tickets.update_one({"_id": ticket_id}, {"$set": ticket})
        await intr.response.send_message("Ticket updated.", ephemeral=True)

    @noteticket.autocomplete("ticket_id")
    async def noteticket_autocomplete(self, _: discord.Interaction, current: str):
        tickets = await self.tickets.find({"title": {"$regex": current}}).to_list(length=88675309)

        return [
            app_commands.Choice(name=ticket["title"], value=ticket["_id"])
            for ticket in tickets
        ]

    @closeticket.autocomplete("ticket_id")
    async def closeticket_autocomplete(self, _: discord.Interaction,
                                       current: str):
        tickets = await self.tickets.find(
            {"status": {"$ne": "CLOSED"},
             "title": {"$regex": current}}).to_list(length=88675309)

        return [
            app_commands.Choice(name=ticket["title"], value=ticket["_id"])
            for ticket in tickets
        ]

    async def validate(self, intr: discord.Interaction, role_ids=None):
        if intr.user.id == self.bot.owner_id:
            return True

        if role_ids:
            for role_id in role_ids:
                role = intr.guild.get_role(role_id)
                if role in intr.user.roles:
                    return True

        await intr.response.send_message(COMMAND_NOT_ALLOWED, ephemeral=True)
        await self.bot.alert_owner("%s tried to use /%s. Check integration permissions" % (intr.user.name,
                                                                                           intr.data.get("name")))
        return False

    async def get_ticket_from_id(self, ticket_id):
        ticket = self.tracked_tickets.get(ticket_id, None)

        if not ticket:
            ticket = await self.tickets.find_one({"_id": ticket_id})

        return ticket

    async def get_ticket_from_channel_id(self, channel_id):
        ticket = self.tracked_tickets.get(channel_id, None)

        if not ticket:
            ticket = await self.tickets.find_one({"channel": channel_id})

            if not ticket:
                return

            if ticket["channel"] not in self.tracked_tickets:
                self.tracked_tickets[channel_id] = [True, ticket]

        return ticket

    async def get_data_from_msg(self, msg: discord.Message):
        data = {
            "user": msg.author.id,
            "time": msg.created_at,
            "id": msg.id,
            "content": msg.content
        }

        self.add_mention_data(data, msg)
        await self.add_reference_data(data, msg)
        await self.add_attachment_data(data, msg)

        return data

    async def add_attachment_data(self, data, msg: discord.Message):
        attachments = []

        if msg.attachments:
            for attachment in msg.attachments:
                if (attachment.content_type and "image" in attachment.content_type) or attachment.size <= 512_000:
                    content = await attachment.read()
                    attachment_data = {
                        "id": attachment.id,
                        "filename": attachment.filename,
                        "url": attachment.url,
                        "content_type": attachment.content_type,
                        "content": base64.encodebytes(content)
                    }
                    attachments.append(attachment_data)

        if attachments:
            data["attachments"] = attachments

    async def add_reference_data(self, data, msg: discord.Message):
        if msg.reference:
            if msg.reference.channel_id == msg.channel.id:
                data["reference"] = msg.reference.message_id
            else:
                channel_id = msg.reference.channel_id
                msg_id = msg.reference.message_id

                ref_channel = await self.bot.fetch_channel(channel_id)
                ref_msg = await ref_channel.fetch_message(msg_id)

                data["reference"] = await self.get_data_from_msg(ref_msg)

    def add_mention_data(self, data, msg: discord.Message):
        mentions = {}

        if msg.mentions:
            mentions["user_mentions"] = [mention.id for mention in msg.mentions]
        if msg.role_mentions:
            mentions["role_mentions"] = [mention.id for mention in msg.role_mentions]
        if msg.channel_mentions:
            mentions["channel_mentions"] = [mention.id for mention in msg.channel_mentions]

        if mentions:
            data["mentions"] = mentions

    async def load_open_ticket_info(self):
        open_tickets = await self.tickets.find({"status": TicketStatus.OPEN.name,
                                                "channel": {"$exists": True}}).to_list(length=88675309)
        self.tracked_tickets = {ticket["channel"]: [False, ticket] for ticket in open_tickets}

    async def sync_tickets(self):
        for k, v in self.tracked_tickets.items():
            if v[0]:
                await self.tickets.update_one({"channel": k}, {"$set": v[1]})
                v[0] = False


class TicketModal(Modal):

    def __init__(self, collection, bot: Eindjeboss,
                 message: discord.Message = None):
        super().__init__(title="Submit a ticket", timeout=600)
        self.collection = collection
        self.message = message
        self.bot = bot

    ticket_title = TextInput(label="Subject", style=discord.TextStyle.short,
                             placeholder="Short, descriptive title goes here")

    description = TextInput(label="Description", style=discord.TextStyle.paragraph, placeholder="Tell us what's up",
                            max_length=1024)

    async def on_submit(self, intr: discord.Interaction):
        ticket_channel_id = await self.bot.get_setting(
            "modmail_channel", None)
        ticket_id = str(uuid.uuid1())[:5]

        tick_type = "report" if self.message else "ticket"
        msg = f"New {tick_type} submitted by {intr.user.display_name}. Respond to it with /handleticket {ticket_id}"

        embed_author = f"Ticket by {intr.user.display_name}"
        embed_title = self.ticket_title.value
        embed_description = self.description.value

        embed = discord.Embed(title=embed_title, description=embed_description, color=discord.Color.red())

        embed.set_author(name=embed_author)

        data = {"_id": ticket_id, "author": intr.user.display_name, "author_id": intr.user.id,
                "title": self.ticket_title.value, "description": self.description.value, "sub_time": int(time.time()),
                "status": TicketStatus.OPEN.name, "messages": []}

        if self.message:
            data["message_id"] = self.message.id
            data["message_content"] = await self.get_msg_data(ticket_id, self.message)
            msg_url = f"[Link]({self.message.jump_url})"
            embed.add_field(name="Reference", value=msg_url)

        self.collection.insert_one(data)
        await intr.response.send_message("Ticket submitted.", ephemeral=True)

        channel = await intr.guild.fetch_channel(ticket_channel_id)
        await channel.send(content=msg, embed=embed)
        lg.info("%s submitted ticket %s", intr.user.name, ticket_id)

    async def on_error(self, intr: discord.Interaction, error: Exception) -> None:
        await intr.response.send_message("There was an error with the ticket. Please try again.", ephemeral=True)
        lg.error(error)

    async def on_timeout(self) -> None:
        return

    async def get_msg_data(self, ticket: str, message: discord.Message):
        data = {"url": message.jump_url, "message_author": message.author.mention}

        if message.content:
            data["content"] = message.content
        if message.attachments:
            paths = []
            for idx, attachment in enumerate(message.attachments, start=1):
                report_dir = f"{self.bot.file_dir}/reports/{ticket}/"
                path = report_dir + f"{idx}_{attachment.filename}"
                os.makedirs(report_dir, exist_ok=True)
                await attachment.save(path)
                paths.append(path)
            data["img_paths"] = paths

        return data


class TicketStatus(Enum):
    OPEN = 1
    IN_PROGRESS = 2
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
    await client.add_cog(Ticket(client))
