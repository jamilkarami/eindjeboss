import discord
import logging as lg
import os
from discord import app_commands
from discord.ext import commands


class Admin(commands.Cog):
    def __init__(self, client: discord.Client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name='logs')
    @app_commands.describe(full="Choose true if you want the full log file.",
                           ln="The number of log lines to send.")
    async def logs(self, intr: discord.Interaction, ln: int = 20,
                   full: bool = False):
        admin_role_id = int(os.getenv("ADMIN_ROLE_ID"))
        admin_role = intr.guild.get_role(admin_role_id)

        if not admin_role or admin_role not in intr.user.roles:
            await intr.response.send_message(
                "You are not allowed to use this command.")
            lg.warn(
                "%s attempted to use /logs. Check integrations permissions.",
                intr.user.name)
            return
        file_dir = os.getenv("FILE_DIR")
        logging_file_name = f"{file_dir}/logs/eindjeboss.log"

        if full:
            await intr.user.send(file=discord.File(logging_file_name))
            await intr.response.send_message("Done.", ephemeral=True)
            lg.info("Sent full log file to %s", intr.user.name)
            return

        log_file = open(logging_file_name)
        lines = log_file.readlines()
        log_lines = lines[-min(len(lines), ln):]

        log_msg = ""
        for line in log_lines:
            if len(log_msg) + len(line) > 2000:
                await intr.user.send(f'```{log_msg}```')
                log_msg = ""
            log_msg = log_msg + line
        await intr.user.send(f'```{log_msg}```')
        await intr.response.send_message("Done.", ephemeral=True)
        lg.info("Sent logs to %s", intr.user.name)


async def setup(client: commands.Bot):
    await client.add_cog(Admin(client))
