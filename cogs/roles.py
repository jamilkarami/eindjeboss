from discord.ext import commands
from discord import app_commands
import discord
import logging
from util.vars.role_vars import ROLE_VARS

class Roles(commands.Cog):
    
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{__name__} Cog is ready")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id not in ROLE_VARS.keys():
            return

        guild = self.client.get_guild(payload.guild_id)
        if payload.emoji.name == ROLE_VARS[payload.message_id][0]:
            role_name = ROLE_VARS[payload.message_id][1]
            role = discord.utils.get(guild.roles, name=role_name)
            await payload.member.add_roles(role)
            logging.info(f"Added {role_name} role for {payload.member.name}")
            return

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.message_id not in ROLE_VARS.keys():
            return

        guild = self.client.get_guild(payload.guild_id)
        member = discord.utils.get(guild.members, id=payload.user_id)
        if payload.emoji.name == ROLE_VARS[payload.message_id][0]:
            role_name = ROLE_VARS[payload.message_id][1]
            role = discord.utils.get(guild.roles, name=role_name)
            await member.remove_roles(role)
            logging.info(f"Removed {role_name} role for {payload.member.name}")
            return

    @app_commands.command(name="focus", description="Limits your view to the conversation channels")
    async def focus(self, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, name="Focus")

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message("Focus mode off. Use /focus again to turn it on.", ephemeral=True)
            logging.info(f"Removed focus role for {interaction.user.name}")
            return
        
        await interaction.user.add_roles(role)
        await interaction.response.send_message("Focus mode on. Use /focus again to turn it off.", ephemeral=True)
        logging.info(f"Added focus role for {interaction.user.name}")
        return

async def setup(bot):
    await bot.add_cog(Roles(bot))