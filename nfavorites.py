import csv
import json
import locale
import os

import cloudscraper
import yaml
from bs4 import BeautifulSoup
from progress.spinner import PixelSpinner

from gettags import get_tags


if not os.path.isfile("set.yaml"):
    with open("set.yaml", "w") as f:
        yaml.dump({"cookid": "", "useragent": ""}, f)
    print("Please edit set.yaml")
    exit()

with open("set.yaml", "r", encoding="utf-8") as f:
    data = yaml.load(f, Loader=yaml.CLoader)
    cookie = data["cookid"]
    useragent = data["useragent"]
    if cookie == "":
        print("Please edit set.yaml")
        exit()

URL = "https://nhentai.net/favorites/"
APIURL = "https://nhentai.net/api/gallery/"

table = [["id", "name", "tags"]]
page_number = 1
all_numbers = []
all_names = []
all_tags = []

locate = locale.getdefaultlocale()[0]
if locate == "zh_TW":
    language = {
        "nodata": "沒有發現離線資料 抓取中請稍後...",
        "nodata2": "抓取完畢",
        "usedata": "使用離線資料",
        "getdata": "抓取資料中...",
        "403": "403 錯誤，可能被 cloudflare 阻擋，請檢查 cookie 是否正確",
        "nologin": "未登入，請先登入",
        "done": "完成",
    }
else:
    language = {
        "nodata": "No offline data found, please wait a moment...",
        "nodata2": "Done",
        "usedata": "Use offline data",
        "getdata": "Getting data...",
        "403": "403 error, maby block by cloudflare , please check if the cookie is correct",
        "nologin": "Not login, please login first",
        "done": "Done",
    }


def banner():
    banner_text = r"""
               _           _        _         ___  _
    _ __   ___| |__  _ __ | |_ __ _(_)        / __\/_\/\   /\ \
    | '_ \ / _ \ '_ \| '_ \| __/ _` | |_____ / _\ //_\\ \ / / \
    | | | |  __/ | | | | | | || (_| | |_____/ /  /  _  \ V /  \
    |_| |_|\___|_| |_|_| |_|\__\__,_|_|     \/   \_/ \_/\_/   \
    """
    print(banner_text)


def make_request(url, method="get", data=None):
    scraper = cloudscraper.create_scraper()
    scraper.headers.update(
        {
            "User-Agent": useragent,
            "Cookie": cookie,
            "Referer": "https://nhentai.net/",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6",
            "Accept-Encoding": "gzip, deflate",
        }
    )

    if method == "get":
        response = scraper.get(url)
    elif method == "post":
        response = scraper.post(url, data=data)

    response.encoding = "utf-8"
    return response


def check_pass():
    response = make_request("https://nhentai.net/")
    with open("debug.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    if response.status_code == 403:
        print(language["403"])
        exit()


banner()
check_pass()

if not os.path.isfile("tag.json"):
    print(language["nodata"])
    get_tags()
    print(language["nodata2"])

print(language["usedata"])
spinner = PixelSpinner(language["getdata"])

while True:
    response = make_request(f"{URL}?page={page_number}")

    if "Abandon all hope, ye who enter here" in response.text:
        print(language["nologin"])
        exit()

    soup = BeautifulSoup(response.text, "html.parser")
    galleries = soup.find_all("div", class_="gallery-favorite")

    if not galleries:
        break

    numbers = [gallery.get("data-id") for gallery in galleries]
    names = [gallery.find("div", class_="caption").get_text() for gallery in galleries]
    tags_raw = [
        gallery.find("div", class_="gallery").get("data-tags") for gallery in galleries
    ]
    tags = [tag_string.split(" ") for tag_string in tags_raw]

    all_numbers.extend(numbers)
    all_names.extend(names)
    all_tags.extend(tags)
    page_number += 1
    spinner.next()

spinner.finish()

with open("tag.json", "r", encoding="utf-8") as f:
    tag_mapping = json.load(f)

for idx, gallery_id in enumerate(all_numbers):
    tag_names = []
    for tag_id in all_tags[idx]:
        if tag_id in tag_mapping:
            tag_names.append(tag_mapping[tag_id])

    tag_string = ", ".join(tag_names)
    table.append([gallery_id, all_names[idx], tag_string])


with open("output.csv", "w", newline="", encoding="utf_8_sig") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerows(table)
print(language["done"])
