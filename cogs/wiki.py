import discord
import logging
from discord import app_commands
from discord.ext import commands
from wikipedia_summary import WikipediaSummary


class Wiki(commands.Cog):

    wiki_summary: WikipediaSummary

    def __init__(self, client):
        self.client = client
        self.wiki_summary = WikipediaSummary()

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name="wiki", description="Search for a page on Wikipedia.")
    async def wiki(self, interaction: discord.Interaction, query: str):
        details = self.wiki_summary.get_summary(query)
        if not details:
            await interaction.response.send_message(f"Could not find page for query: {query}", ephemeral=True)
            return
        try:
            embed = discord.Embed(title=details.title, url=details.url)
            if details.description:
                embed.add_field(name="Description", value=details.description, inline=True)
            embed.add_field(name="Summary", value=details.summary, inline=False)
            embed.set_image(url=details.thumbnail_url)
            await interaction.response.send_message(embed=embed)
            logging.info(f"Sent Wiki page to {interaction.user.name} for query {query}")
            return
        except Exception as e:
            logging.info(f"Failed to send Wiki page to {interaction.user.name} for query {query}")
            print(e)


async def setup(bot):
    await bot.add_cog(Wiki(bot))
