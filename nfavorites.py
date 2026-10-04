import csv
import locale
import os
import sys
import time

import requests
import yaml
from progress.spinner import PixelSpinner


if not os.path.isfile("set.yaml"):
    with open("set.yaml", "w") as f:
        yaml.dump({"apikey": ""}, f)
    print("Please edit set.yaml")
    exit()

with open("set.yaml", "r", encoding="utf-8") as f:
    data = yaml.safe_load(f) or {}
    apikey = data.get("apikey", "")
    if not apikey:
        print("Please edit set.yaml")
        exit()

APIURL = "https://nhentai.net/api/v2"
USERAGENT = "nhentai-favorites/2.0 (https://github.com/phillychi3/nhentai-favorites)"
# Only tags of these types are written to the csv
TAG_TYPES = {"tag"}
TAG_BATCH_SIZE = 100

table = [["id", "name", "tags"]]

locate = locale.getdefaultlocale()[0]
if locate == "zh_TW":
    language = {
        "getdata": "抓取資料中...",
        "gettags": "抓取標籤中...",
        "401": "API key 無效，請檢查 set.yaml",
        "429": "請求過於頻繁，{} 秒後自動重試...",
        "error": "請求失敗",
        "done": "完成",
    }
else:
    language = {
        "getdata": "Getting data...",
        "gettags": "Getting tags...",
        "401": "Invalid API key, please check set.yaml",
        "429": "Rate limited, retrying in {}s...",
        "error": "Request failed",
        "done": "Done",
    }

session = requests.Session()
session.headers.update(
    {
        "User-Agent": USERAGENT,
        "Authorization": f"Key {apikey}",
        "Accept": "application/json",
    }
)


def banner():
    banner_text = r"""
               _           _        _         ___  _
    _ __   ___| |__  _ __ | |_ __ _(_)        / __\/_\/\   /\ \
    | '_ \ / _ \ '_ \| '_ \| __/ _` | |_____ / _\ //_\\ \ / / \
    | | | |  __/ | | | | | | || (_| | |_____/ /  /  _  \ V /  \
    |_| |_|\___|_| |_|_| |_|\__\__,_|_|     \/   \_/ \_/\_/   \
    """
    print(banner_text)


def wait_rate_limit(retry_after):
    try:
        seconds = max(int(retry_after), 1)
    except (TypeError, ValueError):
        seconds = 5
    for remaining in range(seconds, 0, -1):
        sys.stdout.write("\r\x1b[K" + language["429"].format(remaining))
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\r\x1b[K")
    sys.stdout.flush()


def api_get(path, params=None):
    while True:
        response = session.get(f"{APIURL}{path}", params=params, timeout=30)
        if response.status_code == 429:
            wait_rate_limit(response.headers.get("Retry-After"))
            continue
        if response.status_code == 401:
            print(language["401"])
            exit()
        if not response.ok:
            print(f"{language['error']}: {response.status_code} {response.text}")
            exit()
        return response.json()


def get_favorites():
    spinner = PixelSpinner(language["getdata"])
    favorites = []
    page_number = 1
    while True:
        data = api_get("/favorites", {"page": page_number})
        favorites.extend(data["result"])
        spinner.next()
        if page_number >= data["num_pages"]:
            break
        page_number += 1
    spinner.finish()
    return favorites


def get_tag_names(tag_ids):
    spinner = PixelSpinner(language["gettags"])
    tag_ids = sorted(tag_ids)
    tag_mapping = {}
    for i in range(0, len(tag_ids), TAG_BATCH_SIZE):
        batch = tag_ids[i : i + TAG_BATCH_SIZE]
        for tag in api_get("/tags/ids", {"ids": ",".join(map(str, batch))}):
            if tag["type"] in TAG_TYPES:
                tag_mapping[tag["id"]] = tag["name"]
        spinner.next()
    spinner.finish()
    return tag_mapping


banner()
api_get("/user")

favorites = get_favorites()
tag_mapping = get_tag_names({tag_id for g in favorites for tag_id in g["tag_ids"]})

for gallery in favorites:
    tag_names = [tag_mapping[t] for t in gallery["tag_ids"] if t in tag_mapping]
    table.append([gallery["id"], gallery["english_title"], ", ".join(tag_names)])


with open("output.csv", "w", newline="", encoding="utf_8_sig") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerows(table)
print(language["done"])
