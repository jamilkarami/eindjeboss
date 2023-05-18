import logging as lg

import discord
from discord import app_commands
from discord.ext import commands

from util.util import get_file, load_json_file

HELP_TEXT = load_json_file(get_file('help.json'))


class Help(commands.Cog, name="help"):

    def __init__(self, client):
        self.bot = client

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name='help',
                          description="Get help with Arnol\'s commands")
    async def help(self, intr: discord.Interaction):

        await intr.response.send_message(embed=get_main_embed(),
                                         view=MainHelpView(),
                                         ephemeral=True)
        lg.info(f"{intr.user.name} used /help")


class MainHelpView(discord.ui.View):

    def __init__(self):
        super().__init__()

    @discord.ui.button(label="GPT", style=discord.ButtonStyle.blurple)
    async def gpt(self, intr: discord.Interaction, btn: discord.ui.button):
        await intr.response.edit_message(
            content=None, embed=mk_l_embed('GPT'), view=GPTView())

    @discord.ui.button(label="Help", style=discord.ButtonStyle.blurple)
    async def help(self, intr: discord.Interaction, btn: discord.ui.button):
        await intr.response.edit_message(
            content=None, embed=mk_l_embed('Help'), view=HelpView())

    @discord.ui.button(label="Images", style=discord.ButtonStyle.blurple)
    async def images(self, intr: discord.Interaction, btn: discord.ui.button):
        await intr.response.edit_message(
            content=None, embed=mk_l_embed('Images'), view=ImageView())

    @discord.ui.button(label="Music", style=discord.ButtonStyle.blurple)
    async def music(self, intr: discord.Interaction, btn: discord.ui.button):
        await intr.response.edit_message(
            content=None, embed=mk_l_embed('Music'), view=MusicView())

    @discord.ui.button(label="Polls", style=discord.ButtonStyle.blurple)
    async def polls(self, intr: discord.Interaction, btn: discord.ui.button):
        await intr.response.edit_message(
            content=None, embed=mk_l_embed('Polls'), view=PollView())

    @discord.ui.button(label="Reddit", style=discord.ButtonStyle.blurple)
    async def reddit(self, intr: discord.Interaction, btn: discord.ui.button):
        await intr.response.edit_message(
            content=None, embed=mk_l_embed('Reddit'), view=RedditView())

    @discord.ui.button(label="Reminders", style=discord.ButtonStyle.blurple)
    async def rem(self, intr: discord.Interaction, btn: discord.ui.button):
        await intr.response.edit_message(
            content=None, embed=mk_l_embed('Reminders'), view=ReminderView())

    @discord.ui.button(label="RNG", style=discord.ButtonStyle.blurple)
    async def rng(self, intr: discord.Interaction, btn: discord.ui.button):
        await intr.response.edit_message(
            content=None, embed=mk_l_embed('RNG'), view=RNGView())

    @discord.ui.button(label="Translate", style=discord.ButtonStyle.blurple)
    async def tr(self, intr: discord.Interaction, btn: discord.ui.button):
        await intr.response.edit_message(
            content=None, embed=mk_l_embed('Translate'), view=TranslateView())

    @discord.ui.button(label="Misc", style=discord.ButtonStyle.blurple)
    async def misc(self, intr: discord.Interaction, btn: discord.ui.button):
        await intr.response.edit_message(
            content=None, embed=mk_l_embed('Miscellaneous'), view=MiscView())


class CategoryView(discord.ui.View):

    def __init__(self):
        super().__init__()
        self._children = self._children[1:] + [self._children[0]]

    @discord.ui.button(label="Go back", style=discord.ButtonStyle.red)
    async def go_back(self, int: discord.Interaction, btn: discord.ui.Button):
        await int.response.edit_message(content=None,
                                        embed=get_main_embed(),
                                        view=MainHelpView())


class HelpView(CategoryView):

    @discord.ui.button(label="/help", style=discord.ButtonStyle.green,
                       row=0)
    async def help_help(self, intr: discord.Interaction,
                        btn: discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    @discord.ui.button(label="/modmail", style=discord.ButtonStyle.green,
                       row=0)
    async def help_modmail(self, intr: discord.Interaction,
                           btn: discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    def __init__(self):
        super().__init__()
        self.help_text = HELP_TEXT.get('Help')


class GPTView(CategoryView):

    @discord.ui.button(label="/gpt", style=discord.ButtonStyle.green,
                       row=0)
    async def help_gpt(self, intr: discord.Interaction,
                       btn: discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    @discord.ui.button(label="/gptsettings", style=discord.ButtonStyle.green,
                       row=0)
    async def help_gpt_settings(self, intr: discord.Interaction,
                                btn: discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    def __init__(self):
        super().__init__()
        self.help_text = HELP_TEXT.get('GPT')


class ImageView(CategoryView):

    @discord.ui.button(label="/img", style=discord.ButtonStyle.green, row=0)
    async def help_img(self, intr: discord.Interaction,
                       btn: discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    @discord.ui.button(label="!transcribe", style=discord.ButtonStyle.green,
                       row=0)
    async def help_trs(self, intr: discord.Interaction,
                       btn: discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    def __init__(self):
        super().__init__()
        self.help_text = HELP_TEXT.get('Images')


class MiscView(CategoryView):

    @discord.ui.button(label="/focus", style=discord.ButtonStyle.green,
                       row=0)
    async def help_focus(self, intr: discord.Interaction,
                         btn: discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    @discord.ui.button(label="/imdb", style=discord.ButtonStyle.green,
                       row=0)
    async def help_imdb(self, intr: discord.Interaction,
                        btn: discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    @discord.ui.button(label="/nextf1race", style=discord.ButtonStyle.green,
                       row=0)
    async def help_f1(self, intr: discord.Interaction,
                      btn: discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    @discord.ui.button(label="/place", style=discord.ButtonStyle.green,
                       row=0)
    async def help_place(self, intr: discord.Interaction,
                         btn: discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    @discord.ui.button(label="/wiki", style=discord.ButtonStyle.green,
                       row=0)
    async def help_wiki(self, intr: discord.Interaction,
                        btn: discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    def __init__(self):
        super().__init__()
        self.help_text = HELP_TEXT.get('Misc')


class MusicView(CategoryView):

    @discord.ui.button(label="/lyrics", style=discord.ButtonStyle.green, row=0)
    async def help_ly(self, intr: discord.Interaction, btn: discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    @discord.ui.button(label="/spc", style=discord.ButtonStyle.green, row=0)
    async def help_cu(self, intr: discord.Interaction, btn: discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    @discord.ui.button(label="/sp", style=discord.ButtonStyle.green, row=0)
    async def help_sp(self, intr: discord.Interaction, btn: discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    def __init__(self):
        super().__init__()
        self.help_text = HELP_TEXT.get('Music')


class PollView(CategoryView):

    @discord.ui.button(label="/poll", style=discord.ButtonStyle.green, row=0)
    async def help_poll(self, intr: discord.Interaction,
                        btn: discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    @discord.ui.button(label="/yesno", style=discord.ButtonStyle.green, row=0)
    async def help_yesno(self, intr: discord.Interaction,
                         btn: discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    def __init__(self):
        super().__init__()
        self.help_text = HELP_TEXT.get('Polls')


class RedditView(CategoryView):

    @discord.ui.button(label="/randomcat", style=discord.ButtonStyle.green,
                       row=0)
    async def help_rcat(self, intr: discord.Interaction,
                        btn: discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    @discord.ui.button(label="/randomdog", style=discord.ButtonStyle.green,
                       row=0)
    async def help_rdog(self, intr: discord.Interaction,
                        btn: discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    @discord.ui.button(label="/car", style=discord.ButtonStyle.green,
                       row=0)
    async def help_rcar(self, intr: discord.Interaction,
                        btn: discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    @discord.ui.button(label="/hotwheels", style=discord.ButtonStyle.green,
                       row=0)
    async def help_hwheels(self, intr: discord.Interaction,
                           btn: discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    def __init__(self):
        super().__init__()
        self.help_text = HELP_TEXT.get('Reddit')


class ReminderView(CategoryView):

    @discord.ui.button(label="/remindme", style=discord.ButtonStyle.green,
                       row=0)
    async def help_remindme(self, intr: discord.Interaction,
                            btn: discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    @discord.ui.button(label="/myreminders", style=discord.ButtonStyle.green,
                       row=0)
    async def help_myrem(self, intr: discord.Interaction,
                         btn: discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    @discord.ui.button(label="/deletereminder",
                       style=discord.ButtonStyle.green,
                       row=0)
    async def help_delrem(self, intr: discord.Interaction,
                          btn: discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    def __init__(self):
        super().__init__()
        self.help_text = HELP_TEXT.get('Reminders')


class RNGView(CategoryView):

    @discord.ui.button(label="/8ball", style=discord.ButtonStyle.green, row=0)
    async def help_8ball(self, intr: discord.Interaction,
                         btn: discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    @discord.ui.button(label="/chooseforme", style=discord.ButtonStyle.green,
                       row=0)
    async def help_choose(self, intr: discord.Interaction,
                          btn: discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    @discord.ui.button(label="/coin", style=discord.ButtonStyle.green, row=0)
    async def help_coin(self, intr: discord.Interaction,
                        btn: discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    @discord.ui.button(label="/roll", style=discord.ButtonStyle.green, row=0)
    async def help_roll(self, intr: discord.Interaction,
                        btn: discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    def __init__(self):
        super().__init__()
        self.help_text = HELP_TEXT.get('RNG')


class TranslateView(CategoryView):

    @discord.ui.button(label="!tr", style=discord.ButtonStyle.green,
                       row=0)
    async def help_tr(self, intr: discord.Interaction, btn:
                      discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    @discord.ui.button(label="!trimg", style=discord.ButtonStyle.green,
                       row=0)
    async def help_trimg(self, intr: discord.Interaction,
                         btn: discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    @discord.ui.button(label="/translate", style=discord.ButtonStyle.green,
                       row=0)
    async def help_translate(self, intr: discord.Interaction,
                             btn: discord.ui.Button):
        embed = mk_embed(btn.label, self.help_text.get(btn.label), False)
        await intr.response.edit_message(embed=embed)

    def __init__(self):
        super().__init__()
        self.help_text = HELP_TEXT.get('Translate')


async def setup(client: commands.Bot):
    await client.add_cog(Help(client))


def mk_embed(title, fields: dict, inline) -> discord.Embed:
    embed = discord.Embed(title=title)
    for k, v in fields.items():
        if list == type(v):
            v = '\n'.join(v)
        embed.add_field(name=k, value=v, inline=inline)
    return embed


def get_main_embed() -> discord.Embed:
    main_embed = mk_embed('What do you need help with?',
                          HELP_TEXT.get('general').get('modules'), True)
    main_embed.description = '\n'.join(HELP_TEXT.get('general').get('desc'))
    return main_embed


def mk_l_embed(title) -> discord.Embed:
    list_embed = discord.Embed(title=title)
    list_embed.description = "Choose a command for more details."
    return list_embed
