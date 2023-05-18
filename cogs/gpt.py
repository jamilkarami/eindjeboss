import logging as lg
import os

import discord
import openai
from aiocron import crontab
from discord import app_commands
from discord.ext import commands
from openai.error import RateLimitError

usage_reset_cron = "0 0 1 * *"

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

    def __init__(self, client):
        self.bot = client
        self.gptusage = self.bot.dbmanager.get_collection('gptusage')
        self.gptset = self.bot.dbmanager.get_collection('gptsettings')
        openai.api_key = GPT_TOKEN
        crontab(usage_reset_cron, func=self.reset_usage)

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name='gpt', description="Prompt the OpenAI GPT chat")
    async def gpt(self, intr: discord.Interaction, query: str):
        gpt_usage_limit = int(os.getenv('GPT_USAGE_LIMIT'))

        settings = await self.get_gpt_settings(intr.user.id)
        usage = await self.get_gpt_usage(intr.user.id)

        if usage and usage['usage'] >= gpt_usage_limit:
            await intr.response.send_message(LIMIT, ephemeral=True)
            return

        if not settings:
            model_engine = model_engines.get('davinci')
            max_tokens = 256
            await self.save_gpt_settings({'_id': intr.user.id,
                                          'model': model_engine,
                                          'max_tokens': max_tokens})
        else:
            model_engine = settings['model']
            max_tokens = settings['max_tokens']

        em = discord.Embed(title=query, description="Asking ChatGPT...",
                           color=discord.Color.yellow())
        try:
            await intr.response.send_message(embed=em)

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
            await intr.edit_original_response(embed=em)
            ttl_tok = max(int(completion.usage.total_tokens *
                          multipliers.get(model_engine)), 1)
            await self.add_usage(intr.user.id, ttl_tok)
            lg.info(
                f"GPT used by {intr.user.name}. ({ttl_tok} tokens)")
        except RateLimitError as e:
            em.description = "_Server-wide rate limit reached._"
            em.color = discord.Color.red()
            await intr.edit_original_response(embed=em)
            lg.debug(e)

    @app_commands.command(name='gptsettings',
                          description="Set your preferences for GPT Prompts")
    @app_commands.choices(model=model_engines_choices)
    async def setgptsettings(self, int: discord.Interaction,
                             model: app_commands.Choice[str],
                             max_tokens: int = 256):
        if max_tokens > 1024 or max_tokens < 128:
            await int.response.send_message(
                "Max tokens can be between 128 and 1024. Please try again")
            return
        user_settings = {"_id": int.user.id, "model": model.value,
                         "max_tokens": max_tokens}
        await self.save_gpt_settings(user_settings)
        await int.response.send_message("GPT Settings saved.", ephemeral=True)

    async def save_gpt_settings(self, user_settings):
        await self.gptset.update_one({'_id': user_settings.get('_id')},
                                     {"$set": user_settings}, True)

    async def get_gpt_settings(self, user_id):
        return await self.gptset.find_one({'_id': user_id})

    async def add_usage(self, user_id, ttl_tok):
        usage = await self.get_gpt_usage(user_id)

        if usage:
            usage['usage'] = usage['usage'] + ttl_tok
        else:
            usage = {'_id': user_id, 'usage': ttl_tok}

        await self.gptusage.update_one({'_id': user_id}, {"$set": usage}, True)

    async def get_gpt_usage(self, user_id):
        return await self.gptusage.find_one({'_id': user_id})

    async def reset_usage(self):
        return await self.gptusage.drop()


async def setup(client: commands.Bot):
    await client.add_cog(GPT(client))
