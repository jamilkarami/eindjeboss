import ast
import logging as lg
import operator as op
import re

from discord.ext import commands

from util.vars.eind_vars import CHANNEL_IGNORE_LIST

CALC_REGEX = r"(?:calc|calculate) (.{3,})"

operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
             ast.USub: op.neg}


class Utilities(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
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
                lg.info("Calculated expression for %s", message.author.name)
            except TypeError as te:
                lg.error(f"Failed to calculate expression \"{expression}\""
                         f" for {message.author.name}")
                lg.debug(te)
                await message.reply(
                    'Your expression could not be calculated.'
                    ' Please check your formatting.')
            else:
                await message.reply(f"{result}")


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


async def setup(client: commands.Bot):
    await client.add_cog(Utilities(client))
