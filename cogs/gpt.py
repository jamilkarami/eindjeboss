import logging as lg
import os

import discord
from openai import AsyncOpenAI
from openai.types.responses import Response

from discord import app_commands
from discord.ext import commands
from openai._exceptions import RateLimitError

from bot import Eindjeboss

GPT_TOKEN = os.getenv("OPENAI_TOKEN")

aclient = AsyncOpenAI(api_key=GPT_TOKEN)


class GPT(commands.GroupCog, name="gpt"):

    def __init__(self, bot: Eindjeboss):
        self.bot = bot
        self.gptusage = self.bot.dbmanager.get_collection("gptusage")

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
        model_engine = await self.bot.get_setting("gpt_default_model")

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
        completion : Response = await aclient.responses.create(
            model=model_engine,
            input=query,
            max_output_tokens=max_tokens,
        )

        return (
            completion.output_text,
            completion.usage.total_tokens,
            completion.model,
        )


async def setup(client: Eindjeboss):
    await client.add_cog(GPT(client))
