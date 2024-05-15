import logging as lg
import os
from enum import Enum

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

model_engines = {
    "3.5-turbo": "gpt-3.5-turbo",
    "4o": "gpt-4o"
}

multipliers = {
    "gpt-3.5-turbo": 1,
    "gpt-4o": 10
}

aclient = AsyncOpenAI(api_key=GPT_TOKEN)
model_engines_choices = [app_commands.Choice(name=k, value=v) for k, v in model_engines.items()]


class GPT(commands.GroupCog, name="gpt"):

    def __init__(self, bot: Eindjeboss):
        self.bot = bot
        self.gptusage = self.bot.dbmanager.get_collection("gptusage")
        self.gptset = self.bot.dbmanager.get_collection("gptsettings")
        crontab(usage_reset_cron, func=self.reset_usage)
        crontab(context_reset_cron, func=self.reset_context)

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name="chat", description="Prompt the OpenAI GPT chat")
    @app_commands.rename(keep_context="keep-context")
    async def chat(self, intr: discord.Interaction, query: str, keep_context: bool = False):
        gpt_usage_limit = await self.bot.get_setting("gpt_token_limit", 25000)

        em = discord.Embed(title=query, description="Asking ChatGPT...", color=discord.Color.yellow())
        try:
            await intr.response.send_message(embed=em)
            response, tokens, total_usage, model = await self.query_gpt(intr.user, query, gpt_usage_limit, keep_context)

            if response is GptError.CONTEXT_TOO_LARGE:
                em.color = discord.Color.red()
                em.description = "Current context is too large. Please clear it with `/gpt clear`"
                await intr.edit_original_response(embed=em)
                return

            if response is GptError.USAGE_EXCEEDS_LIMIT:
                em.color = discord.Color.red()
                em.description = ("You have exceeded your monthly GPT usage. Please wait til the start of next month."
                                  " Or take ragdoll out for some Takumi.")
                await intr.edit_original_response(embed=em)
                return

            em.color = discord.Color.green()
            em.description = response
            em.set_footer(text=f"{total_usage}/{gpt_usage_limit} (+{tokens}) ({model})")
            await intr.edit_original_response(embed=em)
        except RateLimitError as e:
            em.color = discord.Color.red()
            em.description = "_Server-wide rate limit reached._"
            await intr.edit_original_response(embed=em)
            lg.debug(e)

    @app_commands.command(name="clear",
                          description="Clear GPT history/context")
    async def clear(self, intr: discord.Interaction):
        await self.clear_context(intr.user.id)
        await intr.response.send_message("Context cleared", ephemeral=True)

    @app_commands.command(name="settings",
                          description="Set your preferences for GPT Prompts")
    @app_commands.choices(model=model_engines_choices)
    async def settings(self, int: discord.Interaction, model: app_commands.Choice[str], max_tokens: int = 256):
        if max_tokens > 2048 or max_tokens < 128:
            await int.response.send_message("Max tokens can be between 128 and 2048. Please try again")
            return
        user_settings = {"_id": int.user.id, "model": model.value, "max_tokens": max_tokens}
        await self.save_gpt_settings(user_settings)
        await int.response.send_message("GPT Settings saved.", ephemeral=True)

    async def clear_context(self, user_id: int):
        await self.gptusage.update_one({"_id": user_id}, {"$unset": {"context": ""}})

    @app_commands.command(name="usage", description="Check your total GPT token usage")
    async def usage(self, intr: discord.Interaction):
        limit = await self.bot.get_setting("gpt_token_limit", 25000)
        user_usage = await self.gptusage.find_one({"_id": intr.user.id})

        msg = f"You've used {user_usage['usage']} tokens out of {limit}"
        await intr.response.send_message(msg, ephemeral=True)

    async def query_gpt(self, user, query, gpt_usage_limit, keep_context=False):
        default_context = [{"role": "system", "content": "You're with user %s." % user.id}]

        max_tokens = await self.bot.get_setting("gpt_max_token", 1024)
        default_model = await self.bot.get_setting("gpt_default_model", "3.5-turbo")

        settings = await self.get_gpt_settings(user.id)
        usage = await self.get_gpt_usage(user.id)

        if usage and usage["usage"] >= gpt_usage_limit:
            return GptError.USAGE_EXCEEDS_LIMIT

        if not settings:
            model_engine = model_engines.get(default_model)
            await self.save_gpt_settings({"_id": user.id, "model": model_engine, "max_tokens": max_tokens})
        else:
            model_engine = settings["model"]
            max_tokens = settings["max_tokens"]

        if usage and keep_context:
            context = usage.get("context", default_context)
            token_size = sum([len(msg["content"]) for msg in context])
            if token_size > 3600:
                return GptError.CONTEXT_TOO_LARGE
        else:
            context = [{"role": "user", "content": query}]

        response, ttl_tok, model = await self.get_response(model_engine, context, max_tokens)

        response_msg = {"role": "assistant", "content": response}
        context.append(response_msg)

        total_usage = await self.add_usage(user.id, ttl_tok, context)
        lg.info(f"GPT used by {user.name}. ({ttl_tok} tokens)")
        return response.replace("As an AI language model, ", ""), ttl_tok, total_usage, model

    async def get_response(self, model_engine, context, max_tokens):
        completion = await aclient.chat.completions.create(model=model_engine, messages=context, max_tokens=max_tokens,
                                                           n=1, stop=None, temperature=0.5)

        ttl_tok = max(int(completion.usage.total_tokens * multipliers.get(model_engine)), 1)
        return completion.choices[0].message.content, ttl_tok, completion.model

    async def save_gpt_settings(self, user_settings):
        await self.gptset.update_one({"_id": user_settings.get("_id")}, {"$set": user_settings}, True)

    async def get_gpt_settings(self, user_id):
        return await self.gptset.find_one({"_id": user_id})

    async def add_usage(self, user_id, ttl_tok, context):
        usage = await self.get_gpt_usage(user_id)

        if usage:
            total_usage = usage["usage"] + ttl_tok
            usage["usage"] = total_usage
            usage["context"] = context
        else:
            total_usage = ttl_tok
            usage = {"_id": user_id, "usage": total_usage, "context": context}

        await self.gptusage.update_one({"_id": user_id}, {"$set": usage}, True)
        return total_usage

    async def get_gpt_usage(self, user_id):
        return await self.gptusage.find_one({"_id": user_id})

    async def reset_usage(self):
        return await self.gptusage.drop()

    async def reset_context(self):
        return await self.gptusage.update_many({}, {"$unset": {"context": ""}})


class GptError(Enum):
    USAGE_EXCEEDS_LIMIT = 1
    CONTEXT_TOO_LARGE = 2


async def setup(client: Eindjeboss):
    await client.add_cog(GPT(client))
