import logging as lg
import os

import discord
import openai
from aiocron import crontab
from discord import app_commands
from discord.ext import commands
from openai.error import RateLimitError

from bot import Eindjeboss

GPT_TOKEN = os.getenv("OPENAI_TOKEN")
LIMIT = "You have reached the usage limit for ChatGPT. Please try again later."

usage_reset_cron = "0 0 1 * *"
context_reset_cron = "0 */4 * * *"

model_engines = {
    "3.5-turbo": "gpt-3.5-turbo"
}

multipliers = {
    "gpt-3.5-turbo": 0.1
}

default_context = [{"role": "system",
                    "content": "You are a helpful assistant."}]

model_engines_choices = [app_commands.Choice(name=k, value=v)
                         for k, v in model_engines.items()]


class GPT(commands.Cog, name="gpt"):

    def __init__(self, bot: Eindjeboss):
        self.bot = bot
        self.gptusage = self.bot.dbmanager.get_collection("gptusage")
        self.gptset = self.bot.dbmanager.get_collection("gptsettings")
        openai.api_key = GPT_TOKEN
        crontab(usage_reset_cron, func=self.reset_usage)
        crontab(context_reset_cron, func=self.reset_context)

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name="gpt", description="Prompt the OpenAI GPT chat")
    async def gpt(self, intr: discord.Interaction, query: str):

        em = discord.Embed(title=query, description="Asking ChatGPT...",
                           color=discord.Color.yellow())
        try:
            await intr.response.send_message(embed=em)
            response = await self.query_gpt(intr.user, query)

            em.color = discord.Color.green()
            em.description = response
            await intr.edit_original_response(embed=em)
        except RateLimitError as e:
            em.color = discord.Color.red()
            em.description = "_Server-wide rate limit reached._"
            await intr.edit_original_response(embed=em)
            lg.debug(e)

    @app_commands.command(name="gptdan")
    async def gptdan(self, intr: discord.Interaction, disable: bool = False):
        danprompt = await self.bot.get_setting("danprompt")
        await self.gptusage.update_one({"_id": intr.user.id}, {"$unset": {
            "context": ""
        }})

        if disable:
            await intr.response.send_message("DAN disabled", ephemeral=True)
            return
        await self.query_gpt(intr.user, danprompt)
        await intr.response.send_message("DAN Enabled", ephemeral=True)

    @app_commands.command(name="gptsettings",
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

    async def query_gpt(self, user, query):
        max_tokens = await self.bot.get_setting("gpt_max_token", 1024)
        default_model = await self.bot.get_setting("gpt_default_model",
                                                   "3.5-turbo")
        gpt_usage_limit = await self.bot.get_setting("gpt_token_limit", 10000)

        settings = await self.get_gpt_settings(user.id)
        usage = await self.get_gpt_usage(user.id)

        if usage and usage["usage"] >= gpt_usage_limit:
            return None

        if not settings:
            model_engine = model_engines.get(default_model)
            await self.save_gpt_settings({"_id": user.id,
                                          "model": model_engine,
                                          "max_tokens": max_tokens})
        else:
            model_engine = settings["model"]
            max_tokens = settings["max_tokens"]

        em = discord.Embed(title=query, description="Asking ChatGPT...",
                           color=discord.Color.yellow())

        if usage:
            context = usage.get("context", default_context)
        else:
            context = default_context
        context.append({"role": "user", "content": query})

        response, ttl_tok = await self.get_response(
            model_engine, context, max_tokens)

        em.description = response.replace("As an AI language model, ", "")
        response_msg = {
            "role": "assistant",
            "content": response
        }
        context.append(response_msg)

        await self.add_usage(user.id, ttl_tok, context)
        lg.info(
            f"GPT used by {user.name}. ({ttl_tok} tokens)")
        return response

    async def get_response(self, model_engine, context, max_tokens):
        completion = await openai.ChatCompletion.acreate(
            model=model_engine,
            messages=context,
            max_tokens=max_tokens,
            n=1,
            stop=None,
            temperature=0.5,
        )

        ttl_tok = max(int(completion.usage.total_tokens *
                          multipliers.get(model_engine)), 1)

        return completion.choices[0].message.content, ttl_tok

    async def save_gpt_settings(self, user_settings):
        await self.gptset.update_one({"_id": user_settings.get("_id")},
                                     {"$set": user_settings}, True)

    async def get_gpt_settings(self, user_id):
        return await self.gptset.find_one({"_id": user_id})

    async def add_usage(self, user_id, ttl_tok, context):
        usage = await self.get_gpt_usage(user_id)

        if usage:
            usage["usage"] = usage["usage"] + ttl_tok
            usage["context"] = context
        else:
            usage = {"_id": user_id, "usage": ttl_tok, "context": context}

        await self.gptusage.update_one({"_id": user_id}, {"$set": usage}, True)

    async def get_gpt_usage(self, user_id):
        return await self.gptusage.find_one({"_id": user_id})

    async def reset_usage(self):
        return await self.gptusage.drop()

    async def reset_context(self):
        return await self.gptusage.update_many({}, {"$unset": {"context": ""}})


async def setup(client: commands.Bot):
    await client.add_cog(GPT(client))
