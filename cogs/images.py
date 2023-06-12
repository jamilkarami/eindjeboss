import logging as lg
import os
import shutil
import uuid

import discord
from bing_image_downloader import downloader
from discord import app_commands
from discord.ext import commands

from bot import Eindjeboss


class Images(commands.Cog, name="Images"):

    def __init__(self, bot: Eindjeboss):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @app_commands.command()
    async def img(self, intr: discord.Interaction, query: str):
        await intr.response.defer()
        temp_folder = "temp/%s" % (uuid.uuid4())
        output_folder = "%s/%s" % (temp_folder, query)
        downloader.download(query, limit=1,  output_dir=temp_folder,
                            adult_filter_off=False, force_replace=False,
                            timeout=60, verbose=False)
        img_file = discord.File(os.path.join(output_folder,
                                             os.listdir(output_folder)[0]))

        await intr.followup.send(file=img_file)
        img_file.close()
        shutil.rmtree(temp_folder)
        lg.info("Sent image to %s for query \"%s\"", intr.user.name, query)


async def setup(client: Eindjeboss):
    await client.add_cog(Images(client))
