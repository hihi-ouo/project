from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from PIL import Image, ImageDraw, ImageFont
from datetime import date
from io import BytesIO
from bs4 import BeautifulSoup
from bisect import bisect_right
import discord
from discord.ext import commands
from discord import app_commands
import base64
import requests
import time
import json
import os


def find(by, value):
    return wait.until(EC.element_to_be_clickable((by, value)))

if not os.path.exists("dxdata.json"):
    response = requests.get("https://raw.githubusercontent.com/gekichumai/dxrating/main/packages/dxdata/dxdata.json")
    dx_data = response.json()
    with open("dxdata.json", "w", encoding="utf-8") as f:
        json.dump(dx_data, f, ensure_ascii=False, indent=2)


with open("dxdata.json", "r", encoding="utf-8") as f:
    dx_data = json.load(f)


level_map = {}
for song in dx_data["songs"]:
    title = song["title"]
    new_song = song["isNew"]
    image_name = song["imageName"]
    for sheet in song["sheets"]:
        if sheet["type"] == "dx":
            chart_type = "DX"
        else:
            chart_type = "STANDARD"
        difficulty = sheet["difficulty"]
        level_map[(title, chart_type, difficulty)] = [sheet["internalLevelValue"], image_name]


segaid = input("Please enter your sega id    ")
password = input("Please enter your password    ")



path = (
    "https://lng-tgk-aime-gw.am-all.net/common_auth/login?"
    "site_id=maimaidxex&redirect_url=https://maimaidx-eng.com/"
    "maimai-mobile/&back_url=https://maimai.sega.com/"

)


driver: WebDriver = webdriver.Chrome()
driver.get(path)
wait = WebDriverWait(driver, 10)


find(By.XPATH, "//label[@class='c-form__label--bg agree']").click()
find(By.XPATH, "//span[@class='c-button--openid--segaId']").click()
find(By.NAME, "sid").send_keys(segaid)
find(By.NAME, "password").send_keys(password)
find(By.XPATH, "//button[@class='c-button--login js-agreeSubmit']").click()



selenium_cookies = driver.get_cookies()
driver.quit()


session = requests.Session()
for cookie in selenium_cookies:
    session.cookies.set(cookie['name'], cookie['value'])

headers = {"User-Agent": "hihiouo"}
results = []

try:
    test_response = session.get("https://maimaidx-eng.com/maimai-mobile/home/", headers=headers)
    test_soup = BeautifulSoup(test_response.text, "html.parser")
    if test_soup.select_one(".name_block") is None:
        print("登入失敗，請確認帳號密碼是否正確")
        exit()
    print("登入成功！")
except Exception as e:
    print(f"登入失敗：{e}")
    exit()
 
response = session.get(f"https://maimaidx-eng.com/maimai-mobile/home/ratingTargetMusic/", headers=headers)
soup = BeautifulSoup(response.text, "html.parser")   
difficulties = ["basic", "advanced", "expert", "master", "remaster"]


for row in soup.select(".m_15"):
    if "screw_block" in row.get("class"):
        column = row.get_text(strip=True)
        continue

    name = row.select_one(".music_name_block")
    score = row.select_one(".music_score_block.w_150")
    kind = row.select_one(".music_kind_icon")

    for d in difficulties:
        if f"music_{d}_score_back" in row.get("class"):
            difficulty = d

    if score:

        if "music_dx" in kind.get("src"):
            chart_type = "DX"
        else:
            chart_type = "STANDARD" 
        
        score_text = score.get_text(strip=True)

        results.append({
            "title": name.get_text(strip=True),
            "score": float(score_text[:-1]),
            "kind" : chart_type,
            "difficulty": difficulty,
            "column": column
        })



def image_to_base64(url, session, headers):
    r = session.get(url, headers=headers)
    content_type = r.headers.get("Content-Type", "image/png")
    b64 = base64.b64encode(r.content).decode()
    return f"data:{content_type};base64,{b64}"

# 抓玩家資料
response = session.get("https://maimaidx-eng.com/maimai-mobile/home/", headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

player_name = soup.select_one(".name_block").get_text(strip=True)
trophy      = soup.select_one(".trophy_inner_block span").get_text(strip=True)
rating_val  = soup.select_one(".rating_block").get_text(strip=True)

imgs        = soup.select(".basic_block img")
avatar_url  = imgs[0].get("src")
course_url  = next(i.get("src") for i in imgs if "course" in i.get("src", ""))
class_url   = next(i.get("src") for i in imgs if "class_rank" in i.get("src", ""))
rating_bg_url = soup.select_one(".p_r.p_3 img").get("src")

avatar_b64  = image_to_base64(avatar_url, session, headers)
course_b64  = image_to_base64(course_url, session, headers)
class_b64   = image_to_base64(class_url, session, headers)
rating_bg_b64 = image_to_base64(rating_bg_url, session, headers)


response_np = session.get("https://maimaidx-eng.com/maimai-mobile/collection/nameplate/", headers=headers)
soup_np = BeautifulSoup(response_np.text, "html.parser")

nameplate_url = soup_np.select_one(".collection_setting_block img[src*='NamePlate']").get("src")
nameplate_b64 = image_to_base64(nameplate_url, session, headers)



score_coefficient = [[80, 0.136, "A"], [90, 0.152, "AA"], [94, 0.168, "AAA"], [97, 0.2, "S"], [98, 0.203, "S+"], [99, 0.208, "SS"], [99.5, 0.211, "SS+"], [100, 0.216, "SSS"], [100.5, 0.224, "SSS+"]]
best, new = [], []
dx_icon_b64 = image_to_base64("https://maimaidx-eng.com/maimai-mobile/img/music_dx.png", session, headers)
std_icon_b64 = image_to_base64("https://maimaidx-eng.com/maimai-mobile/img/music_standard.png", session, headers)



for r in results:

    level, image = level_map[(r["title"], r["kind"], r["difficulty"])][0], level_map[(r["title"], r["kind"], r["difficulty"])][1]
    idx = bisect_right(score_coefficient, r["score"], key = lambda x:x[0])

    if idx != 0:
        coefficient = score_coefficient[idx-1][1]
        score_level = score_coefficient[idx-1][2]
    else:
        coefficient = 0
        score_level = "B"

    if idx == 9:
        rating = 100.5 * coefficient * level
    else:
        rating = r["score"] * coefficient * level

    if r["column"] == "Songs for Rating(New)" or r["column"] == "Songs for Rating Selection(New)":
        new.append([r["title"], r["score"], r["difficulty"], level, int(rating), image, score_level, r["kind"]])
    else:
        best.append([r["title"], r["score"], r["difficulty"], level, int(rating), image, score_level, r["kind"]])


best.sort(key = lambda x:x[4], reverse = True)
new.sort(key = lambda x:x[4], reverse = True)



RANK_ICONS = {
    "SSS+": "music_icon_sssp",
    "SSS":  "music_icon_sss",
    "SS+":  "music_icon_ssp",
    "SS":   "music_icon_ss",
    "S+":   "music_icon_sp",
    "S":    "music_icon_s",
    "AAA":  "music_icon_aaa",
    "AA":   "music_icon_aa",
    "A":    "music_icon_a",
}

rank_icon_b64 = {}
for rank, filename in RANK_ICONS.items():
    url = f"https://maimaidx-eng.com/maimai-mobile/img/{filename}.png?ver=1.60"
    rank_icon_b64[rank] = image_to_base64(url, session, headers)

def generate_html(new, best, player_name, trophy, rating_val, avatar_b64, course_b64, class_b64, nameplate_b64, std_icon_b64, rank_icon_b64, bg_path="bg_vertical.jpg"):
    bg_path = os.path.abspath("bg_vertical.jpg").replace("\\", "/")

    DIFF_COLORS = {
        "basic":    "#45c147",
        "advanced": "#ffa500",
        "expert":   "#ff6496",
        "master":   "#b450ff",
        "remaster": "#deb4ff",
    }

    def card_html(song):
        title, score, difficulty, level, rating, image_name, score_level, kind = song
        kind_icon = dx_icon_b64 if kind == "DX" else std_icon_b64
        image_url = f"https://shama.dxrating.net/images/cover/v2/{image_name}.jpg"
        border_color = DIFF_COLORS.get(difficulty, "#b450ff")
        rank_icon = rank_icon_b64.get(score_level, "")

        return f"""
        <div class="card" style="border-color: {border_color};">
            <img class="cover" src="{image_url}" />
            <div class="overlay"></div>
            <img class="kind-icon" src="{kind_icon}" />
            <div class="top-right">{level:.1f}</div>
            <div class="bottom">
                <div class="title">{title}</div>
                <div class="bottom-row">
                    <div class="score">{score:.4f}%</div>
                    <img class="rank-icon" src="{rank_icon}" />
                    <div class="rating">{rating}</div>
                </div>
            </div>
        </div>
        """

    def new_label_html():
        letters = list("NEW SONGS")
        colors  = ["#000000", "#000000", "#000000", "", "#ff4444", "#ff9900", "#eae439", "#33cc33", "#4488ff"]
        spans = ""
        for l, c in zip(letters, colors):
            if l == " ":
                spans += "&nbsp;"
            else:
                spans += f'<span style="color:{c};">{l}</span>'
        return f'<div class="section-label-new">{spans}</div>'

    def section_html(label, songs):
        cards = "".join(card_html(s) for s in songs)
        label_html = new_label_html() if label == "NEW SONGS" else '<div class="section-label-old">OLD SONGS</div>'
        return f"""
        <div class="section">
            {label_html}
            <div class="grid">{cards}</div>
        </div>
        """
    
    today = date.today().strftime("%Y/%m/%d")
    n15_total = sum(s[4] for s in new)
    b35_total = sum(s[4] for s in best)
    n15_avg = round(n15_total / len(new), 2) if new else 0
    b35_avg = round(b35_total / len(best), 2) if best else 0
    
    header_html = f"""
    <div class="header">
        <img class="avatar" src="{avatar_b64}" />
        <div class="player-info">
            <div class="trophy-text">{trophy}</div>
            <div class="player-name">{player_name}</div>
            <div class="badges">
                <div class="rating-badge">
                    <span class="rating-label">でらっくす RATING</span>
                    <span class="rating-num">{rating_val}</span>
                </div>
                <img class="badge-img" src="{course_b64}" />
                <img class="badge-img" src="{class_b64}" />
            </div>
        </div>
        <div class="header-right">
            <div class="score-summary">
                <div class="score-block">
                    <div class="score-num">{n15_total}</div>
                    <div class="score-label">N15</div>
                    <div class="score-avg">avg {n15_avg}</div>
                </div>
                <div class="score-block">
                    <div class="score-num">{b35_total}</div>
                    <div class="score-label">B35</div>
                    <div class="score-avg">avg {b35_avg}</div>
                </div>
            </div>
            <div class="gen-date">{today}</div>
        </div>
    </div>
    """

    new_html  = section_html("NEW SONGS", new)
    best_html = section_html("OLD SONGS", best)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        @font-face {{
            font-family: "NotoSansTC";
            src: url('file:///C:/Windows/Fonts/NotoSansTC-VF.ttf');
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background-image: url('file:///{bg_path}');
            background-size: cover;
            background-position: center;
            padding: 12px;
            font-family: "NotoSansTC", sans-serif;
            width: 1260px;
            overflow: hidden;
        }}
        .section {{ margin-bottom: 12px; }}
        .section-label-new {{
            display: inline-block;
            background: white;
            font-size: 22px;
            font-weight: 900;
            padding: 6px 20px;
            border-radius: 50px;
            margin-bottom: 8px;
            box-shadow: 3px 3px 8px rgba(0,0,0,0.3);
        }}
        .section-label-old {{
            display: inline-block;
            background: #5bc8f5;
            color: white;
            font-size: 22px;
            font-weight: 900;
            padding: 6px 20px;
            border-radius: 50px;
            margin-bottom: 8px;
            box-shadow: 3px 3px 8px rgba(0,0,0,0.3);
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 8px;
        }}
        .card {{
            position: relative;
            width: 100%;
            aspect-ratio: 4 / 3;
            border-radius: 12px;
            border: 5px solid;
            overflow: hidden;
            box-shadow: 4px 4px 10px rgba(0,0,0,0.4);
        }}
        .cover {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        .overlay {{
            position: absolute;
            inset: 0;
            background: rgba(0,0,0,0.2);
        }}
        .top-right {{
            position: absolute;
            top: 6px;
            right: 8px;
            color: white;
            font-size: 18px;
            font-weight: bold;
            background: rgba(0,0,0,0.5);
            padding: 2px 6px;
            border-radius: 4px;
        }}
        .bottom {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(0,0,0,0.6);
            padding: 6px 8px 4px;
            display: flex;
            flex-direction: column;
            gap: 2px;
        }}
        .bottom-row {{
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
        }}
        .title {{
            color: white;
            font-size: 22px;
            font-weight: bold;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .score {{
            color: #ddd;
            font-size: 16px;
            font-weight: 900;
        }}
        .rating {{
            color: white;
            font-size: 32px;
            font-weight: bold;
            line-height: 1;
            flex-shrink: 0;
            margin-left: 8px;
        }}
        .header {{
            display: flex;
            align-items: center;
            gap: 16px;
            border-radius: 16px;
            padding: 12px 16px;
            margin-bottom: 12px;
            background-image: url('{nameplate_b64}');
            background-size: cover;
            background-position: center;
            position: relative;
            overflow: hidden;
        }}
        .header::after {{
            content: '';
            position: absolute;
            inset: 0;
            background: rgba(0,0,0,0.05);
            border-radius: 16px;
            z-index: 0;
        }}
        .header > * {{
            position: relative;
            z-index: 1;
        }}
        .header-right {{
            margin-left: auto;
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 6px;
        }}
        .score-summary {{
            display: flex;
            gap: 16px;
        }}
        .score-block {{
            text-align: center;
        }}
        .score-num {{
            color: white;
            font-size: 28px;
            font-weight: 900;
            text-shadow: 2px 2px 6px rgba(0,0,0,0.8);
        }}
        .score-label {{
            color: white;
            font-size: 13px;
            font-weight: bold;
            text-shadow: 1px 1px 3px rgba(0,0,0,0.8);
        }}
        .score-avg {{
            color: white;
            font-size: 16px;
            font-weight: bold;
            text-shadow: 1px 1px 3px rgba(0,0,0,0.8);
        }}
        .gen-date {{
            color: white;
            font-size: 14px;
            font-weight: bold;
            text-shadow: 1px 1px 3px rgba(0,0,0,0.8);
        }}
        .avatar {{
            width: 100px;
            height: 100px;
            border-radius: 12px;
            border: 3px solid white;
            box-shadow: 3px 3px 8px rgba(0,0,0,0.3);
        }}
        .player-info {{
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}
        .trophy-text {{
            color: white;
            font-size: 14px;
            text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
        }}
        .player-name {{
            color: white;
            font-size: 28px;
            font-weight: 900;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            letter-spacing: 4px;
        }}
        .badges {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .rating-badge {{
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
            padding: 4px 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .rating-label {{
            color: #aaddff;
            font-size: 12px;
            font-weight: bold;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
        }}
        .rating-num {{
            color: white;
            font-size: 24px;
            font-weight: 900;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
        }}
        .badge-img {{
            height: 36px;
        }}
        .kind-icon {{
            position: absolute;
            top: 6px;
            left: 6px;
            height: 24px;
        }}
        .rank-icon {{
            height: 28px;
            flex-shrink: 0;
        }}
    </style>
    </head>
    <body>
    {header_html}
    {new_html}
    {best_html}
    </body>
    </html>
    """

    with open("rating.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("rating.html 已產生")



def screenshot_html():


    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1300,900")
    options.add_argument("--hide-scrollbars")
    driver = webdriver.Chrome(options=options)

    driver.get(f"file:///{os.path.abspath('rating.html')}")
    time.sleep(2)

    width = driver.execute_script("return document.body.scrollWidth")
    height = driver.execute_script("return document.body.scrollHeight")
    driver.set_window_size(width + 20, height + 20)
    time.sleep(1)


    result = driver.execute_cdp_cmd("Page.captureScreenshot", {
        "format": "png",
        "captureBeyondViewport": True,
        "clip": {
            "x": 0, "y": 0,
            "width": width,
            "height": height,
            "scale": 1
        }
    })

    with open("rating.png", "wb") as f:
        f.write(base64.b64decode(result["data"]))

    driver.quit()
    print("rating.png 已產生")


generate_html(new[:15], best[:35], player_name, trophy, rating_val, avatar_b64, course_b64, class_b64, nameplate_b64, std_icon_b64, rank_icon_b64)
screenshot_html()