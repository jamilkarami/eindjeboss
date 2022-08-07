from discord.ext import commands

import logging
from googletrans import Translator
from googletrans.constants import LANGUAGES
from cogs.eind_vars import *

translator = Translator()

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
            dst_msg = TranslateUtil.translate_message(reaction.message, None)

            await user.send(content=src_msg)
            await user.send(content=dst_msg)
            return

    @commands.command(aliases=['tr'])
    async def translate(self, ctx, *args):
        src = None if not args else args[0]
        
        if ctx.message.reference:
            await ctx.message.reference.resolved.reply(TranslateUtil.translate_message(ctx.message.reference.resolved, src))
        else:
            await ctx.message.reply("\"!translate\" can only be used as a reply to another message")
        return


class TranslateUtil():
    def translate_message(message, src):
        translated = translator.translate(message.content) if not src else translator.translate(message.content, src=src)
        lang = LANGUAGES[translated.src]
        return "Translated from (" + lang.capitalize() + "): " + translated.text

async def setup(bot):
    await bot.add_cog(Translate(bot))