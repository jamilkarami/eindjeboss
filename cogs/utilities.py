import ast
import discord
import logging as lg
import operator as op
import os
import re
from discord import app_commands
from discord.ext import commands
from util.vars.eind_vars import CHANNEL_IGNORE_LIST

CALC_REGEX = r"(?:calc|calculate) (.{3,})"

operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
             ast.USub: op.neg}


class Utilities(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user:
            return
        if message.channel.id in CHANNEL_IGNORE_LIST:
            return

        message_content = message.content.lower()

        calc_pattern = re.compile(CALC_REGEX)
        matches = calc_pattern.match(message_content)

        if (matches):
            try:
                expression = matches.group(1)
                result = '{0:.2f}'.format(calculate(expression))
            except TypeError as te:
                lg.error(f"Failed to calculate expression \"{expression}\""
                         f" for {message.author.name}")
                lg.debug(te)
                await message.reply(
                    'Your expression could not be calculated.'
                    ' Please check your formatting.')
            else:
                await message.reply(f"{result}")

    @app_commands.command(name='logs')
    async def logs(self, intr: discord.Interaction, ln: int = 20):
        if intr.user.id != int(os.getenv('RAGDOLL_ID')):
            await intr.response.send_message(
                'You\'re not allowed to use this command.', ephemeral=True)
            lg.info('%s tried to use the /logs command' % intr.user.name)
            return

        log_file = open("%s/logs/eindjeboss.log" % os.getenv('FILE_DIR'))
        lines = log_file.readlines()
        log_lines = lines[-min(len(lines), ln):]

        log_msg = ""
        for line in log_lines:
            if len(log_msg) + len(line) > 2000:
                await intr.user.send('```%s```' % log_msg)
                log_msg = ""
            log_msg = log_msg + line
        await intr.user.send('```%s```' % log_msg)
        await intr.response.send_message(":yes:", ephemeral=True)


def calculate(expression: str):
    node = ast.parse(expression, mode='eval').body
    return eval_(node)


def eval_(node):
    if isinstance(node, ast.Num):
        return node.n
    elif isinstance(node, ast.BinOp):
        return operators[type(node.op)](eval_(node.left), eval_(node.right))
    elif isinstance(node, ast.UnaryOp):
        return operators[type(node.op)](eval_(node.operand))
    else:
        raise TypeError(node)


async def setup(bot):
    await bot.add_cog(Utilities(bot))
