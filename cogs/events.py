import asyncio
import logging as lg
import os
import uuid
from colorsys import hsv_to_rgb, rgb_to_hsv
from typing import List

import discord
from bing_image_downloader import downloader
from colorthief import ColorThief
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from bot import Eindjeboss
from util.util import download_img_from_url

FILE_DIR = os.getenv('FILE_DIR')

# set up static image files
BADGE_FILE = FILE_DIR + "/images/ehv_badge.png"

# set up fonts
SIZE_TITLE = 80
SIZE_TAGS = 48

FONT_TITLE_PATH = FILE_DIR + "/fonts/RobotoFlexVariable.ttf"
FONT_TITLE = ImageFont.truetype(FONT_TITLE_PATH, SIZE_TITLE)
FONT_TITLE.set_variation_by_name('ExtraBlack Italic')

FONT_TAGS_PATH = FILE_DIR + "/fonts/RobotoFlexVariable.ttf"
FONT_TAGS = ImageFont.truetype(FONT_TAGS_PATH, SIZE_TAGS)
FONT_TAGS.set_variation_by_name('Regular')

DESIRED_W = 1230
DESIRED_H = 1400
MAX_TITLE = 16

ALERT = "%s New event added in %s! check it out here: %s"


class Events(commands.Cog):

    def __init__(self, bot: Eindjeboss):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        if thread.parent_id != await self.bot.get_setting("events_forum_id"):
            return
        await self.announce_event(thread)

    @app_commands.command(name="announceevent")
    async def announceevent(self, intr: discord.Interaction,
                            thread: discord.Thread,
                            img_override: str = None):
        await intr.response.defer(ephemeral=True)
        if thread.parent_id != await self.bot.get_setting("events_forum_id"):
            await intr.followup.send(
                "This thread is not in the events forum", ephemeral=True)
            return
        try:
            await self.announce_event(thread, img_override)
            await intr.followup.send('Done.', ephemeral=True)
        except Exception as e:
            lg.exception(e)
            await intr.followup.send("Failed to announce. Check the image.",
                                     ephemeral=True)

    async def announce_event(self, thread: discord.Thread,
                             img: str = None):
        events_forum_id = await self.bot.get_setting("events_forum_id")
        announcement_ch_id = await self.bot.get_setting(
            "event_announcement_channel_id")

        if thread.parent_id != events_forum_id:
            return

        f_ch = await thread.guild.fetch_channel(events_forum_id)

        alert_channel = await thread.guild.fetch_channel(announcement_ch_id)
        ev_rl = discord.utils.get(
            thread.guild.roles,
            id=await self.bot.get_setting("events_role_id"))
        await asyncio.sleep(3)

        img = await get_img(thread) if not img else download_img_from_url(img)

        alert_msg = ALERT % (ev_rl.mention, f_ch.mention, thread.mention)

        output_img = make_ev_img(img, thread.name, thread.applied_tags)
        await alert_channel.send(alert_msg, file=discord.File(output_img))

        os.remove(output_img)


def make_ev_img(img_path: str, title: str, tags: List[str]):

    output_img_filename = 'temp/output_%s' % uuid.uuid4()

    base_img = Image.new('RGBA', size=(DESIRED_W, DESIRED_H),
                         color=(0, 0, 0, 0))
    badge_img = Image.open(BADGE_FILE)

    colorthief = ColorThief(img_path)
    colors = colorthief.get_palette()

    main_color = next((color for color in colors if not is_dark(color)),
                      (255, 255, 255))
    main_color = adjust_saturation(main_color, -100)
    transparent = (0, 0, 0, 0)
    bubbles_color = (23, 23, 23)

    img = Image.open(img_path).convert('RGB')
    size = img.size

    des_w = DESIRED_W - 80
    des_h = DESIRED_H - 180

    mask_rect = Image.new('L', size=(des_w, des_h), color=0)
    draw = ImageDraw.Draw(mask_rect)
    draw.rounded_rectangle((0, 0, des_w, des_h), radius=40, fill=255)

    border_rect = Image.new('RGBA', size=(des_w, des_h), color=0)
    draw = ImageDraw.Draw(border_rect)
    draw.rounded_rectangle((0, 0, des_w, des_h), radius=40, fill=transparent,
                           outline=main_color, width=10)

    if size[0] < des_w:
        ratio = des_w/size[0]
        size = (round(size[0]*ratio), round(size[1]*ratio))
    if size[1] < des_h:
        ratio = des_h/size[1]
        size = (round(size[0]*ratio), round(size[1]*ratio))

    img = img.resize(size)
    img = crop_img(img)
    img = img.resize((des_w, des_h - 30))
    mask_rect = mask_rect.resize(img.size)
    border_rect = border_rect.resize(img.size)

    base_img.paste(img, (60, 95), mask=mask_rect)
    base_img.paste(border_rect, (60, 95), mask=border_rect)

    draw_tag_bubbles(base_img, sorted([tag.name.lower() for tag in tags]),
                     bubbles_color, main_color, FONT_TAGS)
    frames = draw_title_text(base_img, title.upper(), 0, 60, DESIRED_W - 20,
                             main_color)

    # remove disposal parameter when Discord supports APNG
    if frames:
        # use this when Discord supports APNG
        # duration = [1000] + [33] * (len(frames)-2) + [1000]
        duration = 1500
        output_img_filename = output_img_filename + ".gif"
        frames[0].save(output_img_filename, save_all=True,
                       append_images=frames[1:],
                       duration=duration, loop=0, disposal=2,
                       format='gif')
    else:
        base_img = Image.composite(badge_img, base_img, badge_img)
        output_img_filename = output_img_filename + ".png"
        base_img.save(output_img_filename)
    img.close()
    base_img.close()
    badge_img.close()
    os.remove(img_path)

    return output_img_filename


def download_img_from_bing(query):
    temp_folder = "temp/%s" % (uuid.uuid4())
    output_folder = "%s/%s" % (temp_folder, query)
    downloader.download(query, limit=1,  output_dir=temp_folder,
                        adult_filter_off=False, force_replace=False,
                        timeout=60, verbose=False)

    return os.path.join(output_folder, os.listdir(output_folder)[0])


def is_dark(color):
    red = color[0]
    green = color[1]
    blue = color[2]
    darkness = 1.0-(0.299*red + 0.587*green + 0.114*blue)/255.0

    return darkness > 0.5


async def get_img(thread: discord.Thread):
    await asyncio.sleep(3)
    msg = await thread.fetch_message(thread.id)
    if msg.attachments:
        return download_img_from_url(msg.attachments[0].url)
    if msg.embeds:
        for embed in msg.embeds:
            if embed.thumbnail:
                return download_img_from_url(embed.thumbnail.url)
    return download_img_from_bing(thread.name)


def complementary(inp):
    hsv = rgb_to_hsv(inp[0], inp[1], inp[2])
    rgb = hsv_to_rgb((hsv[0] + 0.5) % 1, hsv[1], hsv[2])
    return tuple(int(x) for x in rgb)


def adjust_saturation(inp, val):
    hsv = rgb_to_hsv(inp[0], inp[1], inp[2])
    hsv = (hsv[0], min(hsv[1]*((100+val)/100), 1), hsv[2])
    rgb = hsv_to_rgb(hsv[0], hsv[1], hsv[2])
    return tuple(int(x) for x in rgb)


def adjust_darkness(inp, val):
    hsv = rgb_to_hsv(inp[0], inp[1], inp[2])
    hsv = (hsv[0], hsv[1], hsv[2]*(1-(val/100.0)))
    rgb = hsv_to_rgb(hsv[0], hsv[1], hsv[2])
    return tuple(int(x) for x in rgb)


def draw_tag_bubbles(img, tags, fill, text_color, font):
    start = 60
    high_point = DESIRED_H - 95
    low_point = high_point + 80

    if not tags:
        return

    draw = ImageDraw.Draw(img)

    if len(tags) > 3:
        add = len(tags) - 3
        tags = tags[:3] + [f"+{add}"]

    for tag in tags:
        text_width, _ = font.getsize(tag)
        x1 = start
        x2 = x1 + text_width + 70  # higher hard-coded value -> wider tags
        y1 = high_point
        y2 = low_point

        draw.rounded_rectangle((x1, high_point, x2, low_point), fill=fill,
                               width=2, radius=45)
        draw_bubble_text(img, tag, ((x1+x2)/2, (y1+y2)/2),
                         text_color, FONT_TAGS, 2, fill)
        start = start + text_width + 90  # higher value -> tags further apart


def blur_img(img):
    temp = img.copy()
    temp = temp.filter(ImageFilter.GaussianBlur(3))
    img.paste(temp)


def darken_img(img):
    temp = img.copy()
    enhancer = ImageEnhance.Brightness(temp)

    # reduce brightness (e.g. 0.20 reduces it to 20%)
    temp = enhancer.enhance(0.85)
    img.paste(temp)


def draw_bubble_text(img, text, position, fill, font, stroke_width,
                     stroke_fill):
    draw = ImageDraw.Draw(img)

    draw.text(position, text, fill=fill, font=font, stroke_width=stroke_width,
              stroke_fill=stroke_fill, anchor='mm')


def draw_title_text(img: Image.Image, text, y, min_x, max_x, fill):
    font = FONT_TITLE
    draw = ImageDraw.Draw(img)
    badge_img = Image.open(BADGE_FILE)
    max_length = max_x - min_x
    reset = img.copy()
    bbox = font.getbbox(text)
    length = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1] + 25

    # uncomment this when Discord supports APNG
    # if length > max_length:

    words = text.split(' ')
    texts = split_text(words, MAX_TITLE)

    if len(text) > MAX_TITLE and len(texts) > 1:
        # uncomment this when Discord supports APNG
        # return get_frames(img, text, y, min_x, max_x, fill, height)

        frames = []
        temp_img = Image.new('RGBA', (max_length, height), color=(0, 0, 0, 0))
        textdraw = ImageDraw.Draw(temp_img)

        for tx in texts:
            textdraw.rectangle((0, 0, max_length, height), fill=(0, 0, 0, 0))

            bbox = font.getbbox(tx)
            length = bbox[2] - bbox[0]
            start_pt = max_x - length - 60
            textdraw.text((start_pt, y), tx, fill=fill, font=font)
            img.paste(temp_img, (min_x, y), temp_img)
            img = Image.composite(badge_img, img, badge_img)
            frames += [img.copy()]
            img = reset.copy()

        return frames
    else:
        draw.text((max_x-length, y), text, fill=fill, font=font)
        return None


def split_text(words, chars: int):
    res = []
    curr_cnt = 0
    curr_words = []

    for word in words:
        if len(word) + curr_cnt > chars:
            res += [curr_words]
            curr_words = []
            curr_cnt = 0
        curr_words.append(word)
        curr_cnt += len(word)
    res += [curr_words]
    res = [' '.join(txt) for txt in res]

    if len(res) == 1:
        return [res[0]]
    if len(res) == 2:
        return ["%s..." % res[0], "...%s" % res[-1]]

    res_txt = []
    res_txt.append("%s..." % res[0])
    for txt in res[1:-1]:
        res_txt.append("... %s..." % txt)
    res_txt.append("...%s" % res[-1])
    return res_txt


def crop_img(img):
    width, height = img.size

    if width == height:
        return img
    offset = abs(width-height)//2

    if width > height:
        left = offset
        top = 0
        right = width - offset
        bottom = height
    else:
        left = 0
        top = offset
        right = width
        bottom = height - offset

    return img.crop((left, top, right, bottom))


# use this when Discord supports APNG
def get_frames(img: Image.Image, text, y, min_x, max_x, fill, height):
    font = FONT_TITLE
    badge_img = Image.open(BADGE_FILE)
    max_length = max_x - min_x
    reset = img.copy()
    bbox = font.getbbox(text)
    length = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1] + 30

    frames = []
    temp_img = Image.new('RGBA', (max_length, height), color=(0, 0, 0, 0))

    textdraw = ImageDraw.Draw(temp_img)
    start_pt = 160

    textdraw.text((start_pt, y), text, fill=fill, font=font)
    img.paste(temp_img, (min_x, y))
    img = Image.composite(badge_img, img, badge_img)
    frames += [img.copy()]

    while min_x + start_pt + length > max_x:
        textdraw.rectangle((0, 0, max_length, height), fill=(0, 0, 0, 0))
        textdraw.text((start_pt, y), text, fill=fill, font=font)

        img = reset.copy()
        img.paste(temp_img, (min_x, y), temp_img)
        img = Image.composite(badge_img, img, badge_img)
        frames.append(img.copy())
        start_pt -= 6

    frames += [img.copy()]
    return frames


async def setup(client: commands.Bot):
    await client.add_cog(Events(client))
