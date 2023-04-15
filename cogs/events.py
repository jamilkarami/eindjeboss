import discord
import logging as lg
import os
import time
import urllib.request
import uuid
from bing_image_downloader import downloader
from colorsys import rgb_to_hsv, hsv_to_rgb
from colorthief import ColorThief
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
from typing import List

ANNOUNCEMENT_CH_ID = int(os.getenv('EVENT_ANNOUNCEMENT_CHANNEL_ID'))
EVENTS_FORUM_ID = int(os.getenv('EVENTS_FORUM_ID'))
EVENTS_ROLE_ID = int(os.getenv('EVENTS_ROLE_ID'))

FILE_DIR = os.getenv('FILE_DIR')

# setup masks
MASK_FILE = FILE_DIR + "/images/rect_mask.png"
BORDER_FILE = FILE_DIR + "/images/border.png"

# setup fonts
SIZE_TITLE = 72
SIZE_TAGS = 30

FONT_TITLE_PATH = FILE_DIR + "/fonts/RobotoFlexVariable.ttf"
FONT_TITLE = ImageFont.truetype(FONT_TITLE_PATH, SIZE_TITLE)
FONT_TITLE.set_variation_by_name('Black')

FONT_TAGS_PATH = FILE_DIR + "/fonts/RobotoFlexVariable.ttf"
FONT_TAGS = ImageFont.truetype(FONT_TAGS_PATH, SIZE_TAGS)
FONT_TAGS.set_variation_by_name('Regular')

FONT_STROKE = 5

DESIRED_W = 1230
DESIRED_H = 240

ALERT = "%s New event added in %s! check it out here: %s"


class Events(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        lg.info(f"[{__name__}] Cog is ready")

    @commands.Cog.listener()
    async def on_thread_create(self, th: discord.Thread):
        f_ch = await th.guild.fetch_channel(EVENTS_FORUM_ID)
        if th.parent_id != EVENTS_FORUM_ID:
            return

        alert_channel = await th.guild.fetch_channel(ANNOUNCEMENT_CH_ID)
        ev_rl = discord.utils.get(th.guild.roles, id=EVENTS_ROLE_ID)
        time.sleep(3)

        img = get_img(th)

        alert_msg = ALERT % (ev_rl.mention, f_ch.mention, th.mention)

        output_img = make_ev_img(img, th.name, th.applied_tags)
        await alert_channel.send(alert_msg, file=discord.File(output_img))

        time.sleep(1)
        os.remove(output_img)


def download_img_from_bing(query):
    temp_folder = "temp/%s" % (uuid.uuid4())
    output_folder = "%s/%s" % (temp_folder, query)
    downloader.download(query, limit=1,  output_dir=temp_folder,
                        adult_filter_off=False, force_replace=False,
                        timeout=60, verbose=False)

    return os.path.join(output_folder, os.listdir(output_folder)[0])


def download_img_from_url(url):
    img_id = uuid.uuid4()
    img_filename = "temp/temp_%s.jpg" % img_id

    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', "Mozilla/5.0 (Windows NT 6.1)")]

    urllib.request.install_opener(opener)
    urllib.request.urlretrieve(url, img_filename)

    return img_filename


def make_ev_img(img_path: str, title: str, tags: List[str]):

    output_img_filename = 'temp/output_%s.png' % uuid.uuid4()

    # get complementary color
    color_thief = ColorThief(img_path)
    colors = color_thief.get_palette(color_count=6)
    color = complementary(colors[0])
    color = increase_saturation(color, 100)
    stroke = (230, 230, 230)

    img = Image.open(img_path).convert('RGB')
    size = img.size

    if size[0] < DESIRED_W:
        ratio = DESIRED_W/size[0]
        size = (round(size[0]*ratio), round(size[1]*ratio))
    if size[1] < DESIRED_H:
        ratio = DESIRED_H/size[1]
        size = (round(size[0]*ratio), round(size[1]*ratio))

    # modify background
    img = img.resize(size)
    img = crop_img(img, DESIRED_W, DESIRED_H)
    blur_img(img)
    darken_img(img)

    # Uncomment this when Discord fixes preview scaling
    # img = mask_and_border(img)

    draw_text(img, title.title(), (20, 5), color, FONT_TITLE,
              FONT_STROKE, stroke, True, False)
    draw_tag_bubbles(img, sorted([tag.name for tag in tags[:5]], reverse=True),
                     color, stroke, FONT_TAGS)
    img.save(output_img_filename)
    img.close()
    os.remove(img_path)

    return output_img_filename


def get_img(thread: discord.Thread):
    msg = thread.starter_message
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


def increase_saturation(inp, val):
    hsv = rgb_to_hsv(inp[0], inp[1], inp[2])
    hsv = (hsv[0], min(hsv[1]*((100+val)/100), 1), hsv[2])
    rgb = hsv_to_rgb(hsv[0], hsv[1], hsv[2])
    return tuple(int(x) for x in rgb)


def draw_tag_bubbles(img, tags, fill, stroke, font):
    GAP_W = 20
    GAP_H_LO = DESIRED_H - 15
    GAP_H_HI = DESIRED_H - 65

    if not tags:
        return

    draw = ImageDraw.Draw(img)
    for tag in tags:
        text_width, _ = font.getsize(tag.capitalize())
        x1 = DESIRED_W - GAP_W
        x2 = x1 - 25 - text_width  # higher hard-coded value -> wider tags
        y1 = GAP_H_LO
        y2 = GAP_H_HI

        draw.rounded_rectangle((x2, y2, x1, y1), fill=fill,
                               outline=stroke, width=2, radius=25)
        draw_text(img, tag.capitalize(), ((x1+x2)/2, (y1+y2)/2),
                  stroke, FONT_TAGS, 2, fill, False, True)
        GAP_W = GAP_W + 35 + text_width  # higher value -> tags further apart


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


def mask_and_border(img):
    empty = Image.new('RGBA', img.size, (0, 0, 0, 0))
    mask = Image.open('files/images/rect_mask.png', 'r')
    border = Image.open('files/images/border.png').convert('RGBA')

    trans = Image.composite(img, empty, mask)
    trans = Image.composite(border, trans, border)
    return trans


def draw_text(img, text, position, fill, font, stroke_width,
              stroke_fill, check_size: bool, centered: bool):
    draw = ImageDraw.Draw(img)
    size = font.getsize(text)

    edited = False

    if check_size:
        size = font.getsize(text)
        while font.size > 56 and position[0] + size[0] > DESIRED_W:
            font = ImageFont.truetype(FONT_TITLE_PATH, size=font.size-1)
            font.set_variation_by_name('Black')
            size = font.getsize(text)
            stroke_width = max(font.size//12-1, 0)
        while position[0] + size[0] > DESIRED_W:
            edited = True
            text = text[:-1]
            size = font.getsize(text)
        if edited:
            text = text[:-3] + "..."

    draw.text(position, text, fill=fill, font=font, stroke_width=stroke_width,
              stroke_fill=stroke_fill, anchor="mm" if centered else None)


def crop_img(img, new_width, new_height):
    width, height = img.size

    left = (width - new_width)/2
    top = (height - new_height)/2
    right = (width + new_width)/2
    bottom = (height + new_height)/2

    img = img.crop((left, top, right, bottom))
    return img


async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))
