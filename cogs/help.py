import logging as lg

import discord
from discord import app_commands
from discord.ext import commands

from bot import Eindjeboss

CMD_STYLE = discord.ButtonStyle.green
BK_STYLE = discord.ButtonStyle.red
CAT_STYLE = discord.ButtonStyle.blurple

MORE_DETAILS = "Choose a command for more details."


class Help(commands.Cog, name="help"):

    def __init__(self, bot: Eindjeboss):
        self.bot = bot
        self.helpcoll = self.bot.dbmanager.get_collection("help")

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name="help",
                          description="Get help with Arnol\'s commands")
    async def help(self, intr: discord.Interaction):
        helptext = await self.helpcoll.find_one()

        modules = get_modules(helptext)
        main_embed = mk_embed("What do you need help with?", modules, True)

        disclaimer = "\n".join(helptext["general"]["desc"])
        main_embed.add_field(name="", value=f"_{disclaimer}_", inline=False)

        await intr.response.send_message(embed=main_embed,
                                         view=MainView(helptext, main_embed),
                                         ephemeral=True)
        lg.info(f"{intr.user.name} used /help")


class MainView(discord.ui.View):

    def __init__(self, helptext, parent_embed):
        super().__init__()
        emojis = helptext["general"]["emojis"]
        for k, v in helptext.items():
            if k in ["general", "_id"]:
                continue
            emoji = emojis[k]
            btn = CategoryButton(k, v, self, parent_embed, emoji)
            self.add_item(btn)


class CategoryButton(discord.ui.Button):

    def __init__(self, label, data, parent, parent_embed, emoji):
        super().__init__()
        self.label = "\u2800" + label
        self.data = data
        self.parent = parent
        self.parent_embed = parent_embed
        self.style = CAT_STYLE
        self.emoji = emoji

    async def callback(self, interaction: discord.Interaction):
        title = f"{self.emoji}{self.label}"
        await interaction.response.edit_message(
            content=None, embed=discord.Embed(title=title,
                                              description=MORE_DETAILS),
            view=CategoryView(self.label, self.data, self.parent,
                              self.parent_embed))


class CommandButton(discord.ui.Button):

    def __init__(self, label, data):
        super().__init__()
        self.label = label
        self.data = data
        self.style = CMD_STYLE

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content=None,
                                                embed=mk_embed(self.label,
                                                               self.data,
                                                               False))


class CategoryView(discord.ui.View):

    def __init__(self, label: str, helptext, parent: discord.ui.View,
                 parent_embed: discord.Embed):
        super().__init__()
        self.label = label
        self.helptext = helptext
        self.parent = parent
        self.parent_embed = parent_embed

        for k, v in helptext.items():
            btn = CommandButton(k, v)
            self.add_item(btn)

        back_btn = discord.ui.Button(label="Go back", style=BK_STYLE,
                                     row=len(self._children) // 5)
        back_btn.callback = self.go_back
        self.add_item(back_btn)

    async def go_back(self, int: discord.Interaction):
        await int.response.edit_message(content=None, embed=self.parent_embed,
                                        view=self.parent)


async def setup(client: commands.Bot):
    await client.add_cog(Help(client))


def mk_embed(title, fields: dict, inline) -> discord.Embed:
    embed = discord.Embed(title=title)
    for k, v in fields.items():
        if list == type(v):
            v = "\n".join(v)
        embed.add_field(name=k, value=v, inline=inline)
    return embed


def get_modules(data):
    modules = {}

    for k, v in data.items():
        if k in ["_id", "general"]:
            continue
        modules[k] = ", ".join(v.keys())

    return modules
