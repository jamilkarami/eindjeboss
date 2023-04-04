import discord
import logging
import os
import requests
import uuid
from discord.ext import commands
from discord import app_commands

SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACE_URL = "https://maps.googleapis.com/maps/api/place/details/json"
PHOTOS_URL = "https://maps.googleapis.com/maps/api/place/photo"


class Maps(commands.Cog, name="maps"):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"[{__name__}] Cog is ready")

    @app_commands.command(name="place")
    async def place(self, interaction: discord.Interaction, query: str):
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        eindhoven_coords = os.getenv('COORDS')
        
        search_results = requests.get(SEARCH_URL, params= {'key': api_key, 'location': eindhoven_coords, 'query': query}).json()
        
        place_id = search_results['results'][0]['place_id']
        place_details = requests.get(PLACE_URL, params = {'key': api_key, 'place_id': place_id}).json()['result']


        open_now = place_details.get('opening_hours').get('open_now')
        title = place_details.get('name') + (' (Open)' if open_now else ' (Closed)')
        url = place_details.get('url')
        opening_hours = '\n'.join([x.replace('\u2009', ' ') for x in place_details.get('opening_hours').get('weekday_text')])

        details = {
            'Address': place_details.get('formatted_address'),
            'Phone Number': place_details.get('international_phone_number'),
            'Rating': '%s (%s ratings)' % (place_details.get('rating'), place_details.get('user_ratings_total')),
            'Opening Hours': opening_hours,
            'Website': place_details.get('website'),
        }

        embed = self.make_embed(title, url, details, discord.Color.blue())

        photos = place_details.get('photos')
        if photos:
            photo_reference = photos[0].get('photo_reference')
            place_photo = requests.get(PHOTOS_URL, params = {'key': api_key, 'photo_reference': photo_reference, 'maxwidth': 4000, 'maxheight': 4000}, stream=True)
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
        logging.info('Sent place to %s' % interaction.user.name)

    def make_embed(self, title, url, details, color) -> discord.Embed:
        embed = discord.Embed(title=title, url=url, color=color)
        for k,v in details.items():
            if v:
                embed.add_field(name=k, value=v, inline=k not in ['Opening Hours', 'Address'])
        return embed

async def setup(bot: commands.Bot):
    await bot.add_cog(Maps(bot))
    