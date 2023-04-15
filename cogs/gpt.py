import discord
import logging as lg
import openai
import os
from discord import app_commands
from discord.ext import commands
from openai.error import RateLimitError
from util.util import save_json_file, load_json_file, get_file

model_engines = {
    "ada": "text-ada-001",
    "babbage": "text-babbage-001",
    "curie": "text-curie-001",
    "davinci": "text-davinci-003",
}

multipliers = {
    "text-ada-001": 0.02,
    "text-babbage-001": 0.025,
    "text-curie-001": 0.1,
    "text-davinci-003": 1
}

model_engines_choices = [app_commands.Choice(name=k, value=v)
                         for k, v in model_engines.items()]

GPT_TOKEN = os.getenv('OPENAI_TOKEN')
GPT_SETTINGS_FILE = 'gpt_settings.json'
GPT_USAGE_FILE = 'gpt_usage.json'

LIMIT = "You have reached the usage limit for ChatGPT. Please try again later."


class GPT(commands.Cog, name="gpt"):

    def __init__(self, bot):
        self.bot = bot
        openai.api_key = GPT_TOKEN

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name='gpt', description="Prompt the OpenAI GPT chat")
    async def gpt(self, int: discord.Interaction, query: str):
        gpt_usage_limit = int(os.getenv('GPT_USAGE_LIMIT'))

        settings = get_gpt_settings(int.user.id)
        usage = get_gpt_usage(int.user.id)

        if usage and usage >= gpt_usage_limit:
            await int.response.send_message(LIMIT, ephemeral=True)
            return

        if not settings:
            model_engine = model_engines.get('davinci')
            max_tokens = 256
        else:
            model_engine = settings['model']
            max_tokens = settings['max_tokens']

        em = discord.Embed(title=query, description="Asking ChatGPT...",
                           color=discord.Color.yellow())
        try:
            await int.response.send_message(embed=em)

            completion = openai.Completion.create(
                engine=model_engine,
                prompt=query,
                max_tokens=max_tokens,
                n=1,
                stop=None,
                temperature=0.5,
            )

            response = completion.choices[0].text.strip()

            em.description = response
            em.color = discord.Color.green()
            await int.edit_original_response(embed=em)
            ttl_tok = max(int(completion.usage.total_tokens *
                          multipliers.get(model_engine)), 1)
            add_usage(int.user.id, ttl_tok)
            lg.info(
                f"GPT used by {int.user.name}. ({ttl_tok} tokens)")
        except RateLimitError as e:
            em.description = "_Server-wide rate limit reached._"
            em.color = discord.Color.red()
            await int.edit_original_response(embed=em)
            lg.debug(e)

    @app_commands.command(name='gptsettings',
                          description="Set your preferences for GPT Prompts")
    @app_commands.choices(model=model_engines_choices)
    async def gptsettings(self, int: discord.Interaction,
                          model: app_commands.Choice[str],
                          max_tokens: int = 256):
        if max_tokens > 1024 or max_tokens < 128:
            await int.response.send_message(
                "Max tokens can be between 128 and 1024. Please try again")
            return
        user_settings = {"model": model.value, "max_tokens": max_tokens}
        save_gpt_settings(int.user.id, user_settings)
        await int.response.send_message("GPT Settings saved.", ephemeral=True)


def save_gpt_settings(id, user_settings):
    id = str(id)
    settings = get_gpt_settings(None)
    settings[id] = user_settings
    save_json_file(settings, get_file(GPT_SETTINGS_FILE))


def get_gpt_settings(id):
    settings = load_json_file(get_file(GPT_SETTINGS_FILE))
    if not id:
        return settings
    return settings.get(str(id))


def add_usage(id, tokens):
    id = str(id)
    usage = get_gpt_usage(None)
    if not usage.get(id):
        usage[id] = tokens
    else:
        usage[id] = usage.get(id) + tokens
    save_json_file(usage, get_file(GPT_USAGE_FILE))


def get_gpt_usage(id):
    usage = load_json_file(get_file(GPT_USAGE_FILE))
    if not id:
        return usage
    return usage.get(str(id))


async def setup(bot: commands.Bot):
    await bot.add_cog(GPT(bot))
