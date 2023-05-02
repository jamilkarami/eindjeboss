import discord
import logging as lg
import os
import shutil
import uuid
from bing_image_downloader import downloader
from discord import app_commands
from discord.ext import commands

N_CHANNEL_ID = os.getenv("N_CHANNEL_ID")
CANDY_CHANNEL_ID = os.getenv("CANDY_CHANNEL_ID")
UNSAFE_CHANNELS = [N_CHANNEL_ID, CANDY_CHANNEL_ID]


class Images(commands.Cog, name="Images"):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @app_commands.command()
    async def img(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        temp_folder = "temp/%s" % (uuid.uuid4())
        output_folder = "%s/%s" % (temp_folder, query)
        downloader.download(query, limit=1,  output_dir=temp_folder,
                            adult_filter_off=False, force_replace=False,
                            timeout=60, verbose=False)
        img_file = discord.File(os.path.join(output_folder,
                                             os.listdir(output_folder)[0]))

        await interaction.followup.send(file=img_file)
        img_file.close()
        shutil.rmtree(temp_folder)


async def setup(client: commands.Bot):
    await client.add_cog(Images(client))
