import discord
import logging as lg
import textwrap as tw
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
        lg.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name="wiki",
                          description="Search for a page on Wikipedia.")
    async def wiki(self, intr: discord.Interaction, query: str):
        details = self.wiki_summary.get_summary(query)
        name = intr.user.name
        if not details:
            await intr.response.send_message(
                f"Could not find page for query: {query}", ephemeral=True)
            return
        try:
            await intr.response.send_message(
                embed=self.get_embed_from_wiki_page(details),
                view=WikiView(details.url))
            lg.info(f"Sent Wiki page to {name} for query {query}")
            return
        except Exception as e:
            lg.info(f"Failed to send Wiki page to {name} for query {query}")
            lg.error(e)

    def get_embed_from_wiki_page(self, page_details):
        embed = discord.Embed(title=page_details.title,
                              url=page_details.url,
                              color=discord.Color.teal())
        if page_details.description:
            embed.add_field(name="Description",
                            value=page_details.description,
                            inline=True)
        embed.add_field(name="Summary",
                        value=tw.shorten(page_details.summary, width=1024),
                        inline=False)
        embed.set_image(url=page_details.thumbnail_url)
        return embed


class WikiView(discord.ui.View):

    def __init__(self, url: str):
        super().__init__()
        self.url = url
        self.add_item(discord.ui.Button(label="Wikipedia",
                                        url=self.url,
                                        style=discord.ButtonStyle.url))


async def setup(client: commands.Bot):
    await client.add_cog(Wiki(client))
