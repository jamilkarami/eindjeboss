import json
import os
import urllib.request
import uuid

from colorthief import ColorThief
from table2ascii import PresetStyle
from table2ascii import table2ascii as t2a


def load_json_file(path):
    try:
        with open(path, "rb+") as f:
            return json.loads(f.read())
    except Exception:
        return dict()


def save_json_file(data, path):
    f = open(path, "w")
    output = json.dumps(data, indent=4)
    print(output, file=f)


def tabulate(headers, data, fields):
    body = []

    for item in data:
        body.append([item[field] for field in fields])

    output = t2a(
        header=headers,
        body=body,
        style=PresetStyle.thin_thick_rounded
    )

    return output


def get_file(path):
    return f"{os.getenv('FILE_DIR')}/{path}"


def check_limit(command: str):
    limits = load_json_file(get_file("limits.json"))
    current = limits[command]["current"]
    max = limits[command]["max"]
    if current < max:
        limits[command]["current"] = current + 1
        save_json_file(limits, "limits.json")
        return True
    return False


def download_img_from_url(url, prefix=None):
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', "Mozilla/5.0 (Windows NT 6.1)")]

    urllib.request.install_opener(opener)
    img_filename = urllib.request.urlretrieve(url, prefix)[0]

    return img_filename


def get_colors_from_img(img_url):
    img_path = download_img_from_url(img_url, str(uuid.uuid4()))
    colorthief = ColorThief(img_path)
    palette = colorthief.get_palette()
    os.remove(img_path)

    return palette
