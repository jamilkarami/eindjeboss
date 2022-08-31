from discord.ext import commands
from discord import app_commands
import discord
import logging
from googletrans import Translator
from googletrans.constants import LANGUAGES
from util.vars.eind_vars import *
from typing import Optional

translator = Translator()

TRANSLATE_LANGUAGES = [
    app_commands.Choice(name="English", value="english"),
    app_commands.Choice(name="Dutch", value="dutch"),
    app_commands.Choice(name="German", value="german"),
    app_commands.Choice(name="Arabic", value="arabic"),
    app_commands.Choice(name="French", value="french"),
    app_commands.Choice(name="Spanish", value="spanish"),
    app_commands.Choice(name="Esperanto", value="esperanto"),
]


class Translate(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{__name__} Cog is ready")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.message.author == self.client.user:
            return

        # Translate by reaction
        if reaction.emoji == BOOK_EMOJI:
            src_msg = "You asked me to translate the following message: " + reaction.message.content
            translated = TranslateUtil.translate_message(
                reaction.message.content, None)

            lang = LANGUAGES[translated.src]
            dst_msg = "Translated from (" + \
                lang.capitalize() + "): " + translated.text

            await user.send(content=src_msg)
            await user.send(content=dst_msg)
            return

    @commands.command(aliases=[])
    async def tr(self, ctx, *args):
        src = None if not args else args[0]

        if ctx.message.reference:
            translated = TranslateUtil.translate_message(
                ctx.message.reference.resolved.content, src)
            lang = LANGUAGES[translated.src]
            payload = f"Translated from ({lang.capitalize()}): {translated.text}"
            await ctx.message.reference.resolved.reply(payload)
        else:
            await ctx.message.reply("\"!tr\" can only be used as a reply to another message")
        return

    @app_commands.command(name="translate")
    @app_commands.choices(src=TRANSLATE_LANGUAGES, dst=TRANSLATE_LANGUAGES)
    async def translate(self, interaction: discord.Interaction, text: str, src: app_commands.Choice[str], dst: app_commands.Choice[str]):
        translated = TranslateUtil.translate_message(
            text, src.value, dst.value)
        await interaction.response.send_message(f"Translation of _\"{text}\"_ from _{src.name}_ to _{dst.name}_: {translated.text}")


class TranslateUtil():
    def translate_message(message, src, dst=None):
        if not dst:
            dst = 'english'
        translated = translator.translate(
            message) if not src else translator.translate(message, src=src, dest=dst)
        return translated


async def setup(bot):
    await bot.add_cog(Translate(bot))
