import discord
import logging
from discord.ext import commands
from discord import app_commands

class Help(commands.Cog, name="help"):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name='help', description="Get help with Arnol\'s commands")
    async def help(self, interaction: discord.Interaction):

        await interaction.response.send_message(embed=get_main_embed(), view=MainHelpView(), ephemeral=True)
        logging.info(f"{interaction.user.name} used /help")

class MainHelpView(discord.ui.View):

    def __init__(self):
        super().__init__()

    @discord.ui.button(label="GPT", style=discord.ButtonStyle.blurple)
    async def gpt(self, interaction: discord.Interaction, button: discord.ui.button):
        await interaction.response.edit_message(content=None, embed=get_list_embed('GPT'), view=GPTView())

    @discord.ui.button(label="Images", style=discord.ButtonStyle.blurple)
    async def images(self, interaction: discord.Interaction, button: discord.ui.button):
        await interaction.response.edit_message(content=None, embed=get_list_embed('Images'), view=ImageView())

    @discord.ui.button(label="Music", style=discord.ButtonStyle.blurple)
    async def music(self, interaction: discord.Interaction, button: discord.ui.button):
        await interaction.response.edit_message(content=None, embed=get_list_embed('Music'), view=MusicView())

    @discord.ui.button(label="Polls", style=discord.ButtonStyle.blurple)
    async def polls(self, interaction: discord.Interaction, button: discord.ui.button):
        await interaction.response.edit_message(content=None, embed=get_list_embed('Polls'), view=PollView())

    @discord.ui.button(label="Reddit", style=discord.ButtonStyle.blurple)
    async def reddit(self, interaction: discord.Interaction, button: discord.ui.button):
        await interaction.response.edit_message(content=None, embed=get_list_embed('Reddit'), view=RedditView())

    @discord.ui.button(label="Reminders", style=discord.ButtonStyle.blurple)
    async def reminders(self, interaction: discord.Interaction, button: discord.ui.button):
        await interaction.response.edit_message(content=None, embed=get_list_embed('Reminders'), view=ReminderView())

    @discord.ui.button(label="RNG", style=discord.ButtonStyle.blurple)
    async def rng(self, interaction: discord.Interaction, button: discord.ui.button):
        await interaction.response.edit_message(content=None, embed=get_list_embed('RNG'), view=RNGView())

    @discord.ui.button(label="Translate", style=discord.ButtonStyle.blurple)
    async def translate(self, interaction: discord.Interaction, button: discord.ui.button):
        await interaction.response.edit_message(content=None, embed=get_list_embed('Translate'), view=TranslateView())

    @discord.ui.button(label="Misc", style=discord.ButtonStyle.blurple)
    async def misc(self, interaction: discord.Interaction, button: discord.ui.button):
        await interaction.response.edit_message(content=None, embed=get_list_embed('Miscellaneous'), view=MiscView())

class HelpView(discord.ui.View):
    
    def __init__(self):
        super().__init__()
        self._children = self._children[1:] + [self._children[0]]

    @discord.ui.button(label = "Go back", style = discord.ButtonStyle.red)
    async def go_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=None, embed=get_main_embed(), view=MainHelpView())

class GPTView(HelpView):

    @discord.ui.button(label="/gpt", style=discord.ButtonStyle.green, row=0)
    async def help_gpt(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = "Ask something from ChatGPT"
        expl = "```/gpt [query]```"
        more = '\n'.join(['By default, this relies on a low-intelligence model. You can choose a smarter model using /gptsettings.',
                'Also keep in mind usage is limited on a per-user and a server-wide basis.'])
        embed = make_embed("/gpt", {"Description": desc, "Example": expl, 'Details': more}, False)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="/gptsettings", style=discord.ButtonStyle.green, row=0)
    async def help_gpt_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = "Modify your ChatGPT settings"
        expl = "```/gptsettings [model] [max tokens]```"
        more = '\n'.join(["- Models are ordered from dumbest to smartest. Better answers come from smarter models but they count more towards your personal limit.",
                "- Use the dumber models if you're just messing around. But if you want more serious answers stick to the smarter ones.",
                "- Max tokens is a way to limit your usage. By default it's 256 but you can set it up to 1024. Tokens are basically the number of words in your query, as well as the responses you get.",
                "- Depending on the model you choose, tokens count differently. (A token in Ada counts for much less than a token in Davinci)",
                "", "**Please don't spam this command otherwise you might get _extra_ limited.**"])
        embed = make_embed("/gptsettings", {"Description": desc, "Example": expl, 'Details': more}, False)
        await interaction.response.edit_message(embed=embed)
        
    def __init__(self):
        super().__init__()

class ImageView(HelpView):

    @discord.ui.button(label="/img", style=discord.ButtonStyle.green, row=0)
    async def help_img(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = "Finds an image matching your query. (off of Bing, for reasons)"
        expl = "```/img [query]```"
        embed = make_embed("/img", {"Description": desc, "Example": expl}, False)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="!transcribe", style=discord.ButtonStyle.green, row=0)
    async def help_transcribe(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = "_Attempts_ to transcribe images from the message you reply to."
        expl = "```Reply to a message (containing images) with !transcribe```"
        embed = make_embed("!transcribe", {"Description": desc, "Example": expl}, False)
        await interaction.response.edit_message(embed=embed)
        
    def __init__(self):
        super().__init__()

class MiscView(HelpView):

    @discord.ui.button(label="/focus", style=discord.ButtonStyle.green, row=0)
    async def help_focus(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = "Enables focus mode which hides most channels from your view. Use it if you need to focus."
        expl = "```/focus```"
        more = "To disable it, just use /focus again"
        embed = make_embed("/focus", {"Description": desc, "Example": expl, 'Details': more}, False)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="/imdb", style=discord.ButtonStyle.green, row=0)
    async def help_imdb(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = "Sends a link to a movie/series (off of IMDb) that matches your query the most."
        expl = "```/imdb [query]```"
        embed = make_embed("/imdb", {"Description": desc, "Example": expl}, False)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="/nextf1race", style=discord.ButtonStyle.green, row=0)
    async def help_f1(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = "Gives you time/date details for the next F1 race"
        expl = "```/nextf1race```"
        embed = make_embed("/nextf1race", {"Description": desc, 'Example': expl}, False)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="/place", style=discord.ButtonStyle.green, row=0)
    async def help_place(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = "Finds a place on Google maps matching your query"
        expl = "```/place [query]```"
        more = "By default, this looks for places around Eindhoven. You can change that by including the city/country name in the query."
        embed = make_embed("/place", {"Description": desc, "Example": expl, 'Details': more}, False)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="/wiki", style=discord.ButtonStyle.green, row=0)
    async def help_wiki(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = "Finds an article on Wikipedia matching your query"
        expl = "```/wiki [query]```"
        embed = make_embed("/wiki", {"Description": desc, "Example": expl}, False)
        await interaction.response.edit_message(embed=embed)
        
    def __init__(self):
        super().__init__()

class MusicView(HelpView):

    @discord.ui.button(label="/spc", style=discord.ButtonStyle.green, row=0)
    async def help_spc(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = "Sends a link to the song you're currently listening to on Spotify."
        expl = "```/spc\n\nResponse: https://open.spotify.com/track/3tsD0AXz90ghHzJAvXPHcW?si=fb110d4abd37479d```"
        more = "This will not work if your Spotify is not linked to Discord, or if you're offline (away/busy works fine)"
        embed = make_embed("/spc", {"Description": desc, "Example": expl, 'Details': more}, False)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="/sp", style=discord.ButtonStyle.green, row=0)
    async def help_sp(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = "Sends a link to a song on Spotify that matches your query the most."
        expl = "```/sp Perturbator - Eclipse\n\nResponse: https://open.spotify.com/track/3tsD0AXz90ghHzJAvXPHcW?si=fb110d4abd37479d```"
        embed = make_embed("/sp", {"Description": desc, "Example": expl}, False)
        await interaction.response.edit_message(embed=embed)
        
    def __init__(self):
        super().__init__()

class PollView(HelpView):

    @discord.ui.button(label="/poll", style=discord.ButtonStyle.green, row=0)
    async def help_poll(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = "Create a poll with up to 4 options. The poll is in the form of a message with nubmered reactions."
        expl = "```/poll\n\nResponse: A window pops up where you fill in the information you want.```"
        embed = make_embed("/poll", {"Description": desc, "Example": expl}, False)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="/yesno", style=discord.ButtonStyle.green, row=0)
    async def help_yesno(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = "A shortcut to /poll with yes/no options."
        expl = "```/poll\n\nResponse: A poll with a title and yes/no reactions.```"
        embed = make_embed("/yesno", {"Description": desc, "Example": expl}, False)
        await interaction.response.edit_message(embed=embed)
        
    def __init__(self):
        super().__init__()

class RedditView(HelpView):

    @discord.ui.button(label="/randomcat", style=discord.ButtonStyle.green, row=0)
    async def help_rcat(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = "Self-explanatory. Sends a random cat image off of reddit."
        embed = make_embed("/randomcat", {"Description": desc}, False)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="/randomdog", style=discord.ButtonStyle.green, row=0)
    async def help_rdog(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = "Self-explanatory. Sends a random dog image off of reddit."
        embed = make_embed("/randomdog", {"Description": desc}, False)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="/car", style=discord.ButtonStyle.green, row=0)
    async def help_rcar(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = "Self-explanatory. Sends a random car image off of reddit."
        embed = make_embed("/car", {"Description": desc}, False)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="/hotwheels", style=discord.ButtonStyle.green, row=0)
    async def help_hwheels(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = "Self-explanatory. Sends a random hot wheels image off of reddit."
        embed = make_embed("/hotwheels", {"Description": desc}, False)
        await interaction.response.edit_message(embed=embed)
        
    def __init__(self):
        super().__init__()

class ReminderView(HelpView):

    @discord.ui.button(label="/remindme", style=discord.ButtonStyle.green, row=0)
    async def help_remindme(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = "Creates a reminder for a specific time. Arnol will mention you in the reminders channel when the time comes."
        expl = "```/remindme [time] [message] [repeat yes/no]\nExample: /remindme [in 3 hours] [Drink water] [no]```"
        more = '\n'.join(["The time can be relative to the current time (in X minutes/hours/days) or a specific time (Tuesday at 13:00). Timezone is Amsterdam.",
                "Setting 'repeat' to true will make Arnol remind you every day at the specific time you set."])
        embed = make_embed("/remindme", {"Description": desc, "Example": expl, 'Details': more}, False)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="/myreminders", style=discord.ButtonStyle.green, row=0)
    async def help_myrem(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = "Shows you a list of your reminders."
        expl = "```/myreminders```"
        more = "The response is a table that has reminder ids (you can use those in /deletereminder), the time, and the message you submitted."
        embed = make_embed("/myreminders", {"Description": desc, "Example": expl, 'Details': more}, False)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="/deletereminder", style=discord.ButtonStyle.green, row=0)
    async def help_delrem(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = "Deletes one of your reminders."
        expl = "```/deletereminder [id]```"
        more = "You can get the reminder ID by using /myreminders. This feature is not complete and I'll write a better way to do this Soon:tm:"
        embed = make_embed("/deletereminder", {"Description": desc, "Example": expl, 'Details': more}, False)
        await interaction.response.edit_message(embed=embed)
        
    def __init__(self):
        super().__init__()

class RNGView(HelpView):

    @discord.ui.button(label="/8ball", style=discord.ButtonStyle.green, row=0)
    async def help_8ball(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = "Shake the magic 8 ball."
        expl = "```/8ball\n\nResponse: Magic 8 ball says: I don't think so ❌```"
        more = "Can also be triggered by sending a message starting with 'Hey Arnol, ' (space included) and ending with a question mark (?)"
        embed = make_embed("/8ball", {"Description": desc, "Example": expl, 'Details': more}, False)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="/chooseforme", style=discord.ButtonStyle.green, row=0)
    async def help_choose(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = "Have Arnol choose from a comma-separated list of options."
        expl = "```/chooseforme yes, no, maybe, I don't know\n\nResponse: Maybe```"
        embed = make_embed("/chooseforme", {"Description": desc, "Example": expl}, False)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="/coin", style=discord.ButtonStyle.green, row=0)
    async def help_coin(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = "Flip a coin."
        expl = "```/coin\n\nResponse: You flip a coin. It lands on: Tails.```"
        embed = make_embed("/coin", {"Description": desc, "Example": expl}, False)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="/roll", style=discord.ButtonStyle.green, row=0)
    async def help_roll(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = "Roll a die. (basically a glorified random number generator with a max)"
        expl = "```/roll [max] (default is 20)\n\nResponse: You roll a D20. You get: 5.```"
        embed = make_embed("/roll", {"Description": desc, "Example": expl}, False)
        await interaction.response.edit_message(embed=embed)
        
    def __init__(self):
        super().__init__()

class TranslateView(HelpView):

    @discord.ui.button(label="!tr", style=discord.ButtonStyle.green, row=0)
    async def help_tr(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = "Translates the message that you reply to."
        expl = "```Reply to a message with !tr [src] and Arnol will translate it for you.```"
        more = "[src] is an optional parameter you can pass to choose the source language.\nSometimes the language detection picks up the wrong language."
        embed = make_embed("!tr", {"Description": desc, "Example": expl, 'Details': more}, False)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="!trimg", style=discord.ButtonStyle.green, row=0)
    async def help_trimg(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = "Translates the message (containing image(s)) that you reply to."
        expl = "```Reply to a message with !trimg and Arnol will translate it for you.```"
        embed = make_embed("!trimg", {"Description": desc, "Example": expl}, False)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="/translate", style=discord.ButtonStyle.green, row=0)
    async def help_translate(self, interaction: discord.Interaction, button: discord.ui.Button):
        desc = "Translate a text from one language to another."
        expl = "```/translate [text] [source language] [destination language]\n\nResponse: translated text.```"
        more = "Can also be called by sending a message with the following format: _translate [text] to [language]_\nExample: translate hello to Japanese"
        embed = make_embed("/translate", {"Description": desc, "Example": expl, 'Details': more}, False)
        await interaction.response.edit_message(embed=embed)
        
    def __init__(self):
        super().__init__()


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))

def make_embed(title, fields: dict, inline) -> discord.Embed:
    embed = discord.Embed(title=title)
    for k,v in fields.items():
        embed.add_field(name=k, value=v, inline=inline)
    return embed

def get_main_embed() -> discord.Embed:
    modules = {
        'GPT': '/gpt, /gptsettings',
        'Images': '/img, !transcribe',
        'Misc': '/focus, /imdb, /nextf1race, /place, /wiki',
        'Music': '/sp, /spc',
        'Polls': '/poll, /yesno',
        'Reddit': '/randomcat, /randomdog, /car, /hotwheels',
        'Reminders': '/remindme, /myreminders, /deletereminder',
        'RNG': '/8ball, /chooseforme, /coin, /roll',
        'Translate': '!tr, !trimg, /translate',
    }
    main_embed = make_embed('What do you need help with?', modules, True)
    main_embed.description = '\n'.join(["Keep in mind that maybe not everything related to Arnol is explained here.", 
                      "If you're looking for something related to Arnol that you don't find here, feel free to reach out to the mods/admins."])
    return main_embed

def get_list_embed(title) -> discord.Embed:
    list_embed = discord.Embed(title=title)
    list_embed.description = "Choose a command for more details."
    return list_embed