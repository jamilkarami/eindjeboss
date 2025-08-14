import logging as lg
import os

import discord
from openai import AsyncOpenAI

from aiocron import crontab
from discord import app_commands
from discord.ext import commands
from openai._exceptions import RateLimitError

from bot import Eindjeboss

GPT_TOKEN = os.getenv("OPENAI_TOKEN")
LIMIT = "You have reached the usage limit for ChatGPT. Please try again later."

usage_reset_cron = "0 0 1 * *"
context_reset_cron = "0 */4 * * *"

aclient = AsyncOpenAI(api_key=GPT_TOKEN)


class GPT(commands.GroupCog, name="gpt"):

    def __init__(self, bot: Eindjeboss):
        self.bot = bot
        self.gptusage = self.bot.dbmanager.get_collection("gptusage")
        crontab(usage_reset_cron, func=self.reset_usage)
        crontab(context_reset_cron, func=self.reset_context)

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name="chat", description="Prompt the OpenAI GPT chat")
    async def chat(self, intr: discord.Interaction, query: str):
        em = discord.Embed(
            title=query, description="Asking ChatGPT...", color=discord.Color.yellow()
        )
        try:
            await intr.response.send_message(embed=em)
            response, tokens, model = await self.query_gpt(intr.user, query)

            em.color = discord.Color.green()
            em.description = response
            em.set_footer(text=f"{tokens} ({model})")
            await intr.edit_original_response(embed=em)
        except RateLimitError as e:
            em.color = discord.Color.red()
            em.description = "_Server-wide rate limit reached._"
            await intr.edit_original_response(embed=em)
            lg.debug(e)

    async def query_gpt(self, user, query):
        max_tokens = await self.bot.get_setting("gpt_max_token", 2048)
        model_engine = self.bot.get_setting("gpt_default_model")

        response, ttl_tok, model = await self.get_response(
            model_engine, max_tokens, query
        )

        lg.info(f"GPT used by {user.name}. ({ttl_tok} tokens)")
        return (
            response,
            ttl_tok,
            model,
        )

    async def get_response(self, model_engine, max_tokens, query):
        completion = await aclient.chat.completions.create(
            model=model_engine,
            messages=[{"role": "user", "content": query}],
            max_tokens=max_tokens,
            n=1,
            stop=None,
            temperature=0.5,
        )

        return (
            completion.choices[0].message.content,
            completion.usage.total_tokens,
            completion.model,
        )


async def setup(client: Eindjeboss):
    await client.add_cog(GPT(client))
