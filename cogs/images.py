import logging
import discord
import os
import pytesseract
from discord import app_commands
from discord.ext import commands
from google_images_search import GoogleImagesSearch
from util.util import *

GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_CUSTOM_ENGINE_CX = os.getenv("GOOGLE_SEARCH_CUSTOM_ENGINE_CX")
N_CHANNEL_ID = os.getenv("N_CHANNEL_ID")
CANDY_CHANNEL_ID = os.getenv("CANDY_CHANNEL_ID")
UNSAFE_CHANNELS = [N_CHANNEL_ID, CANDY_CHANNEL_ID]
GOOGLE_SEARCH_LIMIT_ENTRY = "GoogleSearch"

gis = GoogleImagesSearch(GOOGLE_SEARCH_API_KEY, GOOGLE_SEARCH_CUSTOM_ENGINE_CX)


class Images(commands.Cog, name="Images"):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"[{__name__}] Cog is ready")

    @app_commands.command()
    async def img(self, interaction: discord.Interaction, query: str):
        if not check_limit(GOOGLE_SEARCH_LIMIT_ENTRY):
            await interaction.response.send_message("This command has reached its daily usage limit. You can use it "
                                                    "again tomorrow.", ephemeral=True)
            return
        search_params = self.get_search_params(query, interaction.channel_id)
        gis.search(search_params=search_params)
        if not gis.results():
            await interaction.response.send_message(f"No images found for search query: {query}. Try something else.", ephemeral=True)
            return
        await interaction.response.send_message(gis.results()[0].url)

    def get_search_params(self, query: str, channel: int):
        safety = 'off' if channel in UNSAFE_CHANNELS else 'high'
        search_params = {
            'q': query,
            'num': 1,
            'fileType': 'jpg',
            'rights': 'cc_publicdomain',
            'safe': safety
        }
        return search_params

    @commands.command(aliases=[])
    async def transcribe(self, ctx):
        if ctx.message.reference:
            imgs = []
            msg = ""
            for attachment in ctx.message.reference.resolved.attachments:
                if "image" in attachment.content_type:
                    imgname = f"temp/{attachment.filename}"
                    await attachment.save(imgname)
                    imgs.append(imgname)
            try:
                for idx, img in enumerate(imgs, start=1):
                    payload = (
                        f"**Image {idx}**\n```{pytesseract.image_to_string(img)}```"
                    )
                    msg = msg + payload + "\n\n"
            except pytesseract.TesseractError:
                logging.error("Failed to transcribe text from image")
            finally:
                os.remove(img)

            await ctx.message.reference.resolved.reply(msg)


async def setup(bot: commands.Bot):
    await bot.add_cog(Images(bot))
