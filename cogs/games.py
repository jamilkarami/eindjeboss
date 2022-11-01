from discord.ext import commands
from discord import app_commands
import discord
import logging
from util.util import *
from util.vars.eind_vars import *

MODERATOR_ROLE = "Bruh"


class Games(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name="addgame")
    async def add_game(self, interaction: discord.Interaction, game: str):
        if not check_user_has_role(interaction.user, MODERATOR_ROLE):
            await interaction.response.send_message("You are not allowed to use this command.", ephemeral=True)
            return

        games = load_json_file(get_file(GAME_FILE))

        for key in games.keys():
            if game.lower() == key.lower():
                await interaction.response.send_message("This game is already in the list.", ephemeral=True)
                return

        games[game] = []
        save_json_file(games, get_file(GAME_FILE))
        await interaction.response.send_message(f"{game} added to games list.", ephemeral=True)
        logging.info(f"{game} added to games list.")
        return

    @app_commands.command(name="removegame")
    async def remove_game(self, interaction: discord.Interaction, game: str):
        if not check_user_has_role(interaction.user, MODERATOR_ROLE):
            await interaction.response.send_message("You are not allowed to use this command.", ephemeral=True)
            return

        games = load_json_file(get_file(GAME_FILE))

        for key in games.keys():
            if game.lower() == key.lower():
                games.pop(key)
                save_json_file(games, get_file(GAME_FILE))
                await interaction.response.send_message(f"{key} removed from games list.", ephemeral=True)
                logging.info(f"{key} removed from games list.")
                return

        await interaction.response.send_message("This game is not in the list.", ephemeral=True)
        return

    @app_commands.command(name="addmetogame")
    async def add_user_to_game(self, interaction: discord.Interaction, game: str):
        await interaction.response.send_message("This command is under development.", ephemeral=True)

    @app_commands.command(name="removemefromgame")
    async def remove_user_from_game(self, interaction: discord.Interaction, game: str):
        await interaction.response.send_message("This command is under development.", ephemeral=True)

    @app_commands.command(name="taggame")
    async def tag_game(self, interaction: discord.Interaction, game: str):
        await interaction.response.send_message("This command is under development.", ephemeral=True)


def check_user_has_role(user: discord.Member, role_name: str):
    for role in user.roles:
        if role.name == role_name:
            return True
    return False


async def setup(bot: commands.Bot):
    await bot.add_cog(Games(bot))
