import itertools
import logging as lg
import random
import re

import discord
from bardapi import Bard as bd
from discord import app_commands
from discord.ext import commands

from bot import Eindjeboss

FTD = "Click the button to receive the full text."


class Bard(commands.Cog):

    def __init__(self, bot: Eindjeboss):
        self.bot = bot
        self.tickets = self.bot.dbmanager.get_collection('tickets')

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name="bard",
                          description="Chat with the Google Bard AI Chatbot")
    async def bard(self, intr: discord.Interaction, query: str):
        token = await self.bot.get_setting("bard_token")
        em = discord.Embed(title=query, description="Asking Bard...",
                           color=discord.Color.yellow())

        await intr.response.send_message(embed=em)
        lg.info("%s asked Bard (query: %s)", intr.user.name, query)

        bard = bd(token=token)

        answer = bard.get_answer(query)
        bard_output: str = answer['content']
        em.color = discord.Color.green()

        view = None
        img_links = answer.get("images")

        bard_output = re.sub(r"\[Images? of.*]\n", "", bard_output)
        bard_output = bard_output.replace("\n\n\n", "\n\n")

        if len(bard_output) > 1024:
            lines = bard_output.split("\n")

            desc = ""
            idx = 0
            while idx < len(lines) and len(lines[idx]) + len(desc) < 1024:
                desc = desc + lines[idx] + "\n"
                idx += 1

            em.description = desc[:1020] + "\n..."

            em.set_footer(text=FTD)
            og_msg = await intr.original_response()
            view = BardView(bard_output, og_msg.jump_url)
        else:
            em.description = bard_output

        if img_links:
            embeds = [em]
            em.url = random.choice(answer.get("links"))
            for _, link in enumerate(itertools.islice(img_links, 3)):
                em_cp = em.copy()
                em_cp.set_image(url=link)
                # discord.File(data, f"{str(uuid4())[:5]}.jpg"))
                embeds.append(em_cp)

        await intr.edit_original_response(embeds=embeds, view=view)

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
