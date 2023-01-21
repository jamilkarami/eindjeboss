import discord
import logging
import os
import pytesseract
import re
from discord.ext import commands
from discord import app_commands
from googletrans import Translator
from googletrans.constants import LANGUAGES
from util.vars.eind_vars import *

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

TRANSLATE_PROMPT_REGEX = r"(?:tr|translate) (.+) to (.+)"


class Translate(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.ctx_menu = app_commands.ContextMenu(
            name='Translate Message',
            callback=self.translate_context,
        )
        self.client.tree.add_command(self.ctx_menu)

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"[{__name__}] Cog is ready")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.client.user:
            return
        if message.channel.id in CHANNEL_IGNORE_LIST:
            return

        message_content = message.content.lower()

        calc_pattern = re.compile(TRANSLATE_PROMPT_REGEX)
        matches = calc_pattern.match(message_content)

        if(matches):
            try:
                req = matches.group(1)
                lang = matches.group(2)
                translated = TranslateUtil.translate_text(req, src='auto', dst=lang)
            except ValueError as e:
                logging.error(f'Failed to translate \"{req}\" to {lang} for {message.author.name}')
                logging.debug(e)
                await message.reply('Destination language invalid. Please check for typos.')
            else:
                await message.reply(f"{translated.text}")


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.emoji.name != BOOK_EMOJI:
            return
        message = await self.client.get_channel(payload.channel_id).fetch_message(payload.message_id)
        translated = TranslateUtil.translate_text(message.content, None)

        lang = LANGUAGES[translated.src]

        translate_msg = f"You asked me to translate the following message: ```{message.content}```\nTranslated from ({lang.capitalize()}): ```{translated.text}```"

        await payload.member.send(content=translate_msg)
        logging.info(
            f"Sent translation to {payload.member.name} for message \"{message.content}\" by {message.author.name}")

    async def translate_context(self, interaction: discord.Interaction, message: discord.Message):
        translated = TranslateUtil.translate_text(message.content, None)

        lang = LANGUAGES[translated.src]

        translate_msg = f"Translation for \"{message.content}\" from ({lang.capitalize()}):\n\n{translated.text}"

        await interaction.response.send_message(content=translate_msg, ephemeral=True)
        logging.info(
            f"Sent translation to {interaction.user.name} for message \"{message.content}\" by {message.author.name}")

    @commands.command(aliases=[])
    async def tr(self, ctx, *args):
        src = None if not args else args[0]

        if ctx.message.reference:
            translated = TranslateUtil.translate_text(ctx.message.reference.resolved.content, src)
            lang = LANGUAGES[translated.src].capitalize()
            payload = f"Translated from ({lang}): {translated.text}"
            await ctx.message.reference.resolved.reply(payload)
            return
        await ctx.message.reply("\"!tr\" can only be used as a reply to another message")

    @commands.command(aliases=[])
    async def trimg(self, ctx, *args):
        src = None if not args else args[0]

        if ctx.message.reference:
            imgs = []
            msg = ""
            for attachment in ctx.message.reference.resolved.attachments:
                if "image" in attachment.content_type:
                    imgname = f"temp/{attachment.filename}"
                    os.makedirs(os.path.dirname(imgname), exist_ok=True)
                    await attachment.save(imgname)
                    imgs.append(imgname)
            for idx, img in enumerate(imgs, start=1):
                translated = TranslateUtil.translate_text(TranslateUtil.cleanup(pytesseract.image_to_string(img)), src)
                lang = LANGUAGES[translated.src].capitalize()
                payload = f"**Image {idx}**\n_Translated from ({lang}):_\n```{translated.text}```"
                msg = msg + payload + "\n\n"
                os.remove(img)
            
            await ctx.message.reference.resolved.reply(msg)

    @app_commands.command(name="translate", description="Translate a text from one language to another.")
    @app_commands.choices(src=TRANSLATE_LANGUAGES, dst=TRANSLATE_LANGUAGES)
    async def translate(self, interaction: discord.Interaction, text: str, src: app_commands.Choice[str],
                        dst: app_commands.Choice[str]):
        translated = TranslateUtil.translate_text(text, src.value, dst.value)
        await interaction.response.send_message(f"Translation of _\"{text}\"_ from _{src.name}_ to _{dst.name}_: {translated.text}")


class TranslateUtil:
    @staticmethod
    def translate_text(message, src, dst=None):
        if not dst:
            dst = 'english'
        translated = translator.translate(message) if not src else translator.translate(message, src=src, dest=dst)

        return translated

    @staticmethod
    def cleanup(text: str):
        text = text.replace("\n\n", "\n---\n")
        text = text.replace("\n", " ")
        text = text.replace("---", "\n---\n")
        return text

async def setup(bot):
    await bot.add_cog(Translate(bot))
