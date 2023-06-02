import logging as lg
import os
import uuid

import discord
import requests as rq
from discord import app_commands
from discord.ext import commands

from bot import Eindjeboss

SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACE_URL = "https://maps.googleapis.com/maps/api/place/details/json"
PHOTOS_URL = "https://maps.googleapis.com/maps/api/place/photo"


class Maps(commands.Cog, name="maps"):

    def __init__(self, bot: Eindjeboss):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name="place")
    async def place(self, interaction: discord.Interaction, query: str):
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        eindhoven_coords = await self.bot.get_setting("eindhoven_coords")

        search_results = rq.get(SEARCH_URL,
                                params={'key': api_key,
                                        'location': eindhoven_coords,
                                        'query': query}).json()

        place_id = search_results['results'][0]['place_id']
        pl_det = rq.get(PLACE_URL,
                        params={'key': api_key,
                                'place_id': place_id}).json()['result']

        open_now = pl_det.get('opening_hours').get('open_now')
        title = pl_det.get('name') + (' (Open)' if open_now else ' (Closed)')
        url = pl_det.get('url')
        opening_hours = '\n'.join(
            [x.replace('\u2009', ' ')
             for x in pl_det.get('opening_hours').get('weekday_text')])

        details = {
            'Address': pl_det.get('formatted_address'),
            'Phone Number': pl_det.get('international_phone_number'),
            'Rating': '%s (%s ratings)' % (pl_det.get('rating'),
                                           pl_det.get('user_ratings_total')),
            'Opening Hours': opening_hours,
            'Website': pl_det.get('website'),
        }

        embed = self.make_embed(title, url, details, discord.Color.blue())

        photos = pl_det.get('photos')
        if photos:
            photo_reference = photos[0].get('photo_reference')
            place_photo = rq.get(PHOTOS_URL,
                                 params={'key': api_key,
                                         'photo_reference': photo_reference,
                                         'maxwidth': 4000,
                                         'maxheight': 4000}, stream=True)
            photo_name = 'temp_%s.jpg' % uuid.uuid4()
            with open(photo_name, 'wb') as img:
                img.write(place_photo.content)

            file = discord.File(photo_name, filename="image.png")
            embed.set_image(url="attachment://image.png")
            await interaction.response.send_message(file=file, embed=embed)
            file.close()
            os.remove(photo_name)
        else:
            await interaction.response.send_message(embed=embed)
        lg.info('Sent place to %s' % interaction.user.name)

    def make_embed(self, title, url, details, color) -> discord.Embed:
        embed = discord.Embed(title=title, url=url, color=color)
        for k, v in details.items():
            if v:
                embed.add_field(name=k, value=v,
                                inline=k not in ['Opening Hours', 'Address'])
        return embed


async def setup(client: commands.Bot):
    await client.add_cog(Maps(client))
