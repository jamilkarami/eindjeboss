import logging as lg
import os
import re

import deepl
import discord
from discord import app_commands
from discord.ext import commands

from bot import Eindjeboss
from util.vars.eind_vars import CHANNEL_IGNORE_LIST, DEEPL_LANGUAGE_CODES, DEEPL_LANGUAGE_NAMES

translator = deepl.Translator(os.getenv("DEEPL_API_KEY"))

TRANSLATE_LANGUAGES = [
    app_commands.Choice(name="English", value="EN"),
    app_commands.Choice(name="Dutch", value="NL"),
    app_commands.Choice(name="German", value="DE"),
    app_commands.Choice(name="Arabic", value="AR"),
    app_commands.Choice(name="French", value="FR"),
    app_commands.Choice(name="Spanish", value="SP"),
    app_commands.Choice(name="Italian", value="IT"),
]

TRANSLATE_PROMPT_REGEX = r"(?:tr|translate) (.+) to (.+)"


class Translate(commands.Cog):

    def __init__(self, bot: Eindjeboss):
        self.bot = bot
        self.ctx_menu = app_commands.ContextMenu(name='Translate Message', callback=self.translate_context)
        self.bot.tree.add_command(self.ctx_menu)

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author == self.bot.user:
            return
        if msg.channel.id in CHANNEL_IGNORE_LIST:
            return

        message_content = msg.content.lower()

        translate_re = re.compile(TRANSLATE_PROMPT_REGEX)
        matches = translate_re.match(message_content)

        if matches:
            try:
                req = matches.group(1)
                lang = matches.group(2)
                target_lang = DEEPL_LANGUAGE_NAMES.get(lang.lower())
                if not target_lang:
                    raise ValueError(f"Destination language **{lang}** not found.")
                translated = TranslateUtil.translate_text(req, src=None, dst=target_lang)
            except ValueError as e:
                name = msg.author.name
                lg.error(f"Failed to translate \"{req}\" to {lang} for {name}")
                lg.debug(e)
                await msg.reply('Destination language invalid. Check typos.')
            else:
                await msg.reply(f"{translated[0]}")
                lg.info("Translated text for %s", msg.author.name)

    async def translate_context(self, intr: discord.Interaction, msg: discord.Message):
        tr = TranslateUtil.translate_text(msg.content, None)

        src = f"**{msg.content}**"
        dst = f"**{tr[0]}**"
        lng = f"**{DEEPL_LANGUAGE_CODES.get(tr[1]).capitalize()}**"

        await intr.response.send_message(content=f"Translation for {src} from {lng}: {dst}", ephemeral=True)
        lg.info(f"Sent translation to {intr.user.name} for message {msg.content} by {msg.author.name}")

    @app_commands.command(name="translate", description="Translate a specific text.")
    @app_commands.choices(src=TRANSLATE_LANGUAGES, dst=TRANSLATE_LANGUAGES)
    async def translate(self, intr: discord.Interaction, text: str,
                        src: app_commands.Choice[str] = None, dst: app_commands.Choice[str] = None):
        src_lang = src.value if src else None
        dst_lang = dst.value if dst else "EN"
        tr = TranslateUtil.translate_text(text, src_lang, dst_lang)

        res_src = DEEPL_LANGUAGE_CODES.get(tr[1]).capitalize()
        res_dst = DEEPL_LANGUAGE_CODES.get(dst_lang).capitalize()

        await intr.response.send_message(f"Translation of _\"{text}\"_ from _{res_src}_ to _{res_dst}_: {tr[0]}")
        lg.info(f"Translated text for {intr.user.name}")


class TranslateUtil:
    @staticmethod
    def translate_text(message, src, dst=None):
        # source takes "EN", destination takes "EN-GB"
        if not dst or dst == "EN":
            dst = "EN-GB"
        translated = translator.translate_text(message, target_lang=dst) if not src \
            else translator.translate_text(message, source_lang=src, target_lang=dst)

        return translated.text, translated.detected_source_lang

    @staticmethod
    def cleanup(text: str):
        text = text.replace("\n\n", "\n---\n")
        text = text.replace("\n", " ")
        text = text.replace("---", "\n---\n")
        return text


async def setup(client: Eindjeboss):
    await client.add_cog(Translate(client))
