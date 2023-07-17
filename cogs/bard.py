import logging as lg

import discord
from bardapi import Bard as bd
from discord import app_commands
from discord.ext import commands

from bot import Eindjeboss

FTD = "Click the button to receive the full text. This expires in 3 minutes"


class Bard(commands.Cog):

    def __init__(self, bot: Eindjeboss):
        self.bot = bot
        self.tickets = self.bot.dbmanager.get_collection('tickets')

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name="bard",
                          description="Chat with the Google Bard AI Chatbot")
    @app_commands.rename(keep_context="keep-context")
    async def bard(self, intr: discord.Interaction, query: str,
                   keep_context: bool = False):
        token = await self.bot.get_setting("bard_token")
        em = discord.Embed(title=query, description="Asking Bard...",
                           color=discord.Color.yellow())

        await intr.response.send_message(embed=em)
        lg.info("%s asked Bard (query: %s)", intr.user.name, query)

        if keep_context:
            bard = bd(token=token, conversation_id=str(intr.user.id))
        else:
            bard = bd(token=token)

        bard_output = bard.get_answer(query)['content']
        em.color = discord.Color.green()

        if len(bard_output) > 1024:

            lines = bard_output.split("\n")

            description = ""
            idx = 0
            while len(lines[idx]) + len(description) < 1024:
                description = description + lines[idx] + "\n"
                idx += 1

            em.description = description[:1020] + "\n..."

            em.set_footer(text=FTD)
            og_msg = await intr.original_response()
            view = BardView(bard_output, og_msg.jump_url)
            await intr.edit_original_response(embed=em, view=view)
        else:
            em.description = bard_output
            await intr.edit_original_response(embed=em)

        lg.info("Bard responsed to %s (query: %s)", intr.user.name, query)


class BardView(discord.ui.View):

    def __init__(self, full_text: str, jump_url: str):
        super().__init__(timeout=None)
        self.full_text = full_text
        self.jump_url = jump_url

    @discord.ui.button(style=discord.ButtonStyle.blurple,
                       label="Send Full Text")
    async def send_full_text(self, intr: discord.Interaction,
                             button: discord.ui.Button):
        lines = self.full_text.split("\n")

        header = f"Here is the full text you asked for ({self.jump_url}):"
        await intr.user.send(header, suppress_embeds=True)
        msg = ""
        for line in lines:
            if len(msg) + len(line) > 2000:
                await intr.user.send(msg)
                msg = ""
            msg = msg + line + "\n"
        await intr.user.send(msg)
        await intr.response.send_message("Done.", ephemeral=True)
        lg.info("Sent full text of message %s to %s",
                self.jump_url, intr.user.name)


async def setup(client: commands.Bot):
    await client.add_cog(Bard(client))
