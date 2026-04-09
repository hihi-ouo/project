from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from cryptography.fernet import Fernet
from datetime import date
from bs4 import BeautifulSoup
from bisect import bisect_right
import discord
from discord import app_commands
import asyncio
import base64
import requests
import time
import json
import os


# =====================
# 常數
# =====================
SCORE_COEFFICIENT = [
    [80,  0.136, "A"],
    [90,  0.152, "AA"],
    [94,  0.168, "AAA"],
    [97,  0.2,   "S"],
    [98,  0.203, "S+"],
    [99,  0.208, "SS"],
    [99.5,0.211, "SS+"],
    [100, 0.216, "SSS"],
    [100.5,0.224,"SSS+"],
]

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

DIFF_COLORS = {
    "basic":    "#45c147",
    "advanced": "#ffa500",
    "expert":   "#ff6496",
    "master":   "#b450ff",
    "remaster": "#deb4ff",
}

LOGIN_URL = (
    "https://lng-tgk-aime-gw.am-all.net/common_auth/login?"
    "site_id=maimaidxex&redirect_url=https://maimaidx-eng.com/"
    "maimai-mobile/&back_url=https://maimai.sega.com/"
)

HEADERS = {"User-Agent": "hihiouo"}


# =====================
# 金鑰與加密
# =====================
class CredentialManager:
    KEY_FILE = "secret.key"
    CREDENTIALS_FILE = "credentials.json"

    def __init__(self):
        self.fernet = Fernet(self._load_or_create_key())

    def _load_or_create_key(self) -> bytes:
        if os.path.exists(self.KEY_FILE):
            with open(self.KEY_FILE, "rb") as f:
                return f.read()
        key = Fernet.generate_key()
        with open(self.KEY_FILE, "wb") as f:
            f.write(key)
        return key

    def _encrypt(self, text: str) -> str:
        return self.fernet.encrypt(text.encode()).decode()

    def _decrypt(self, text: str) -> str:
        return self.fernet.decrypt(text.encode()).decode()

    def save(self, user_id: int, segaid: str, password: str):
        data = self._load_file()
        data[str(user_id)] = {
            "segaid":   self._encrypt(segaid),
            "password": self._encrypt(password)
        }
        self._save_file(data)

    def load(self, user_id: int):
        data = self._load_file()
        entry = data.get(str(user_id))
        if entry is None:
            return None
        return {
            "segaid":   self._decrypt(entry["segaid"]),
            "password": self._decrypt(entry["password"])
        }

    def delete(self, user_id: int):
        data = self._load_file()
        data.pop(str(user_id), None)
        self._save_file(data)

    def _load_file(self) -> dict:
        if not os.path.exists(self.CREDENTIALS_FILE):
            return {}
        with open(self.CREDENTIALS_FILE, "r") as f:
            return json.load(f)

    def _save_file(self, data: dict):
        with open(self.CREDENTIALS_FILE, "w") as f:
            json.dump(data, f)
    
    def save_background(self, user_id: int, bg_path: str):
        data = self._load_file()
        if str(user_id) not in data:
            data[str(user_id)] = {}
        data[str(user_id)]["bg_path"] = bg_path
        self._save_file(data)

    def load_background(self, user_id: int) -> str:
        data = self._load_file()
        entry = data.get(str(user_id))
        if entry is None:
            return "bg_vertical.jpg"
        return entry.get("bg_path", "bg_vertical.jpg")


# =====================
# 資料管理
# =====================
class MaimaiData:
    def __init__(self):
        self.level_map = {}
        self._load_dxdata()


    # 抓取DXrating的json檔
    def _load_dxdata(self):
        if not os.path.exists("dxdata.json"):  # 判斷是否抓取過(檢測資料夾中的dxdata.json是否存在)
            print("下載 dxdata.json...")
            response = requests.get(
                "https://raw.githubusercontent.com/gekichumai/dxrating/main/packages/dxdata/dxdata.json"
            )
            dx_data = response.json() #將request接受到的內容解析成字典/列表的方式存進dx_data
            with open("dxdata.json", "w", encoding="utf-8") as f:
                json.dump(dx_data, f, ensure_ascii=False, indent=2)
                # open() 裡面的"w"對應寫入(也會覆蓋)，"r"對應讀取
                # dump會將字典的內容轉成json，load則是反過來
                # ensure_ascii = False 是因為有日文字體，indent則是行距，不影響程式本身但方便查看dxdata.json的內容

        with open("dxdata.json", "r", encoding="utf-8") as f:
            dx_data = json.load(f)

        for song in dx_data["songs"]:
            title = song["title"]
            image_name = song["imageName"]
            for sheet in song["sheets"]:
                chart_type = "DX" if sheet["type"] == "dx" else "STANDARD"
                difficulty = sheet["difficulty"]
                self.level_map[(title, chart_type, difficulty)] = [
                    sheet["internalLevelValue"],
                    image_name,
                ]
        # 將原本dxdata大量的資訊只保留
        # 標題(title), 歌曲圖片url(image_name), 新/舊歌(chart_type), 歌曲難度(expert/master之類的)(difficulty), 確切定數(internalLevelValue)
        # 並存在level_map裡面(前三者當作key, 後兩者是value)

    # 根據已知的歌曲名稱等資訊回傳確切定數和圖片url(方便抓取縮圖)
    def get_level_and_image(self, title, kind, difficulty):
        entry = self.level_map.get((title, kind, difficulty))
        if entry:
            return entry[0], entry[1]
        return None, None

    @staticmethod #靜態方法，不會有self參數所以也不能修改物件和類別的狀態，通常用在傳入參數運算
    # 這邊便是只傳入score和level來計算這首歌玩家獲得的rating
    def calc_rating(score, level):
        idx = bisect_right(SCORE_COEFFICIENT, score, key=lambda x: x[0])
        # 使用二分搜確認score是在甚麼區間並回傳idx(像是99.38就在99到99.5之間)
        if idx == 0:
            return 0, "B"
        # 雖然說maimai裡面還有C和D的分數線，不過通常這些分數並不會進入b35或n15，所以統一不做計算(回傳0)
        coefficient = SCORE_COEFFICIENT[idx - 1][1]
        score_level = SCORE_COEFFICIENT[idx - 1][2]
        base = 100.5 if idx == len(SCORE_COEFFICIENT) else score
        return int(base * coefficient * level), score_level
        # maimai rating的計算方式是將score(例:99.38) * 係數(寫在SCORE_COEFFICIENT裡) * 確切定數(例:13.8)
        # 然而若是score超過100.5就統一以100.5計算(最高可以到101，也就是理論值)


# =====================
# 登入與資料抓取
# =====================
class MaimaiClient:
    def __init__(self, data: MaimaiData):
        self.data = data
        self.session = requests.Session()
        self.player_info = {}
        self.new = []
        self.best = []

    def login(self, segaid: str, password: str) -> bool:
        driver = webdriver.Chrome()
        driver.get(LOGIN_URL)
        wait = WebDriverWait(driver, 10)

        # 使用until()搭配EC.element_to_be_clickable確保程式不會因為網路問題而跳過任何一次操作
        # 具體來說就是讓程式碼在固定時間內(我設定10秒)不斷嘗試我所要求的操作(click()或send_keys())，只要成功了就會跳到下一行程式碼
        def find(by, value):
            return wait.until(EC.element_to_be_clickable((by, value)))


        # 這邊的value基本上就是操作一遍登入流程，需要點擊或輸入內容的f12內容(或者可以右鍵找到檢查來確保沒抓錯class)
        # 使用XPATH是因為其定位較精確，不會抓取到其他內容
        try: 
            find(By.XPATH, "//label[@class='c-form__label--bg agree']").click()
            find(By.XPATH, "//span[@class='c-button--openid--segaId']").click()
            find(By.NAME, "sid").send_keys(segaid)
            find(By.NAME, "password").send_keys(password)
            find(By.XPATH, "//button[@class='c-button--login js-agreeSubmit']").click()
            time.sleep(2)
        finally:     
            selenium_cookies = driver.get_cookies()
            driver.quit() # 這邊因為已經抓到cookie了，所以直接關閉網頁即可

        # 將獲得的cookie保留name和value以便讓我在self.session.get()特定網址時可以直接進入
        # 因為網站透過回傳的cookie得知了你的身分，便不需要再登入一次
        for cookie in selenium_cookies:
            self.session.cookies.set(cookie["name"], cookie["value"])

        # 前面以finally強制get_cookies()，這邊判斷進入網站後能否獲得class裡面有name_block的內容
        # 若是沒有則表示並未取得使用者cookie，也就表示沒登入成功，即輸出登入失敗
        try:
            resp = self.session.get(
                "https://maimaidx-eng.com/maimai-mobile/home/", headers=HEADERS
            )
            soup = BeautifulSoup(resp.text, "html.parser")
            # 將獲得的html資訊定義至BeautifulSoup()的物件中，後面的"html.parser"是解析器
            # 這樣soup的內容大致就是前面那個網站打開f12會看到的內容，我們便可從其中抓取所需的歌曲成績等資訊
            if soup.select_one(".name_block") is None:
                print("登入失敗，請確認帳號密碼是否正確")
                return False
            print("登入成功！")
            return True
        # 若是出現異常則會將異常內容文字輸出，方便進行檢查和debug
        except Exception as e:
            print(f"登入失敗：{e}")
            return False

    # 將已知的圖片url轉成base64的格式，回傳的內容貼進HTML的<img src = "">即可顯示圖片
    # 之所以不直接使用url是因為其中有些圖片需要cookie才能存取    
    def image_to_base64(self, url: str) -> str:
        r = self.session.get(url, headers=HEADERS)
        content_type = r.headers.get("Content-Type", "image/png")   
        b64 = base64.b64encode(r.content).decode()
        return f"data:{content_type};base64,{b64}"

    # 抓取玩家基本資料(大多數是player_info的圖片)
    def fetch_player_info(self):
        resp = self.session.get(
            "https://maimaidx-eng.com/maimai-mobile/home/", headers=HEADERS
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        # 由於前面使用requests.Session()且有紀錄cookie到self.session裡，之後的每一次get()特定網址都不須再登入
        # 另外使用headers是因為經過測試maimaidx net會擋，必須設定一個使用者假裝進行登入
        # 這邊抓取的頁面就是player_info的部分

        imgs = soup.select(".basic_block img")
        avatar_url  = imgs[0].get("src")
        course_url  = next(i.get("src") for i in imgs if "course" in i.get("src", ""))
        class_url   = next(i.get("src") for i in imgs if "class_rank" in i.get("src", ""))


        resp_np = self.session.get(
            "https://maimaidx-eng.com/maimai-mobile/collection/nameplate/",
            headers=HEADERS,
        )
        soup_np = BeautifulSoup(resp_np.text, "html.parser")
        nameplate_url = soup_np.select_one(
            ".collection_setting_block img[src*='NamePlate']"
        ).get("src")

        self.player_info = {
            "name":        soup.select_one(".name_block").get_text(strip=True),
            "trophy":      soup.select_one(".trophy_inner_block span").get_text(strip=True),
            "rating_val":  soup.select_one(".rating_block").get_text(strip=True),
            "avatar_b64":  self.image_to_base64(avatar_url),
            "course_b64":  self.image_to_base64(course_url),
            "class_b64":   self.image_to_base64(class_url),
            "nameplate_b64": self.image_to_base64(nameplate_url),
            # dx_icon和std_icon都是固定的圖片，所以可以直接把url複製進程式裡不用每次都抓
            "dx_icon_b64": self.image_to_base64(
                "https://maimaidx-eng.com/maimai-mobile/img/music_dx.png"
            ),
            "std_icon_b64": self.image_to_base64(
                "https://maimaidx-eng.com/maimai-mobile/img/music_standard.png"
            ),
            "rank_icon_b64": {
                rank: self.image_to_base64(
                    f"https://maimaidx-eng.com/maimai-mobile/img/{filename}.png?ver=1.60"
                )
                for rank, filename in RANK_ICONS.items()
            },
        }

    # 抓取歌曲成績並存進results陣列裡
    # 接著再根據其是新/舊歌存進best和new，並以換算的rating由大到小排序
    def fetch_scores(self):
        resp = self.session.get(
            "https://maimaidx-eng.com/maimai-mobile/home/ratingTargetMusic/",
            headers=HEADERS,
        )
        soup = BeautifulSoup(resp.text, "html.parser")

        results = []
        column = ""
        difficulty = ""
        difficulties = ["basic", "advanced", "expert", "master", "remaster"]

        # select()是找所有指定的項目，所以會形成一個list，select_one()只會找第一個出現的，在確保要找的東西只有1個的時候用select_one()比較快
        # 這邊".m_15"找所有的歌曲成績(.是class的意思)
        for row in soup.select(".m_15"):
            if "screw_block" in row.get("class"):
                column = row.get_text(strip=True) # strip = True可以將前後的空格刪掉
                continue

            name  = row.select_one(".music_name_block")
            score = row.select_one(".music_score_block.w_150")
            kind  = row.select_one(".music_kind_icon") # 新/舊歌

            # 確認歌曲難度
            for d in difficulties:
                if f"music_{d}_score_back" in row.get("class"):
                    difficulty = d

            if score: # 確保有抓到成績
                chart_type = "DX" if "music_dx" in kind.get("src") else "STANDARD"
                score_text = score.get_text(strip=True)
                results.append({
                    "title":      name.get_text(strip=True),
                    "score":      float(score_text[:-1]),
                    "kind":       chart_type,
                    "difficulty": difficulty,
                    "column":     column,
                })
                # get_text()可以抓到那格裡面的文字內容

        self.new, self.best = [], []
        for r in results:
            level, image = self.data.get_level_and_image(
                r["title"], r["kind"], r["difficulty"]
            )
            if level == None:
                continue

            rating, score_level = self.data.calc_rating(r["score"], level)

            # 這邊舉例說明entry裡的內容
            # ["don't figh the music", 100.1021, master, 14.1, 304, 圖片url(我懶得查), SSS, "DX"]
            # 這邊有紀錄score_level(SSS)是因為可以用前面在player_info建立好的"rank_icon"得到圖片
            entry = [r["title"], r["score"], r["difficulty"], level, rating, image, score_level, r["kind"]]

            if r["column"] in ("Songs for Rating(New)", "Songs for Rating Selection(New)"):
                self.new.append(entry)
            else:
                self.best.append(entry)

        self.new.sort(key=lambda x: x[4], reverse=True)
        self.best.sort(key=lambda x: x[4], reverse=True)


# =====================
# 圖片生成
# =====================
class MaimaiImageGenerator:
    def __init__(self, client: MaimaiClient, bg_path: str = "bg_vertical.jpg"):
        self.client = client
        self.bg_path = os.path.abspath(bg_path).replace("\\", "/")

    def generate(self):
        self._generate_html()
        self._screenshot()

    def _card_html(self, song):
        title, score, difficulty, level, rating, image_name, score_level, kind = song
        p = self.client.player_info
        kind_icon  = p["dx_icon_b64"] if kind == "DX" else p["std_icon_b64"]
        rank_icon  = p["rank_icon_b64"].get(score_level)
        image_url  = f"https://shama.dxrating.net/images/cover/v2/{image_name}.jpg"
        border_color = DIFF_COLORS.get(difficulty)

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

    def _new_label_html(self):
        letters = list("NEW SONGS")
        colors  = ["#000000","#000000","#000000","","#ff4444","#ff9900","#eae439","#33cc33","#4488ff"]
        spans = "".join(
            "&nbsp;" if l == " " else f'<span style="color:{c};">{l}</span>'
            for l, c in zip(letters, colors)
        )
        return f'<div class="section-label-new">{spans}</div>'

    def _section_html(self, label, songs):
        cards = "".join(self._card_html(s) for s in songs)
        label_html = (
            self._new_label_html()
            if label == "NEW SONGS"
            else '<div class="section-label-old">OLD SONGS</div>'
        )
        return f"""
        <div class="section">
            {label_html}
            <div class="grid">{cards}</div>
        </div>
        """

    def _generate_html(self):
        p = self.client.player_info
        new  = self.client.new[:15]
        best = self.client.best[:35]

        today     = date.today().strftime("%Y/%m/%d")
        n15_total = sum(s[4] for s in new)
        b35_total = sum(s[4] for s in best)
        n15_avg   = round(n15_total / len(new),  2) if new  else 0
        b35_avg   = round(b35_total / len(best), 2) if best else 0

        header_html = f"""
        <div class="header">
            <img class="avatar" src="{p['avatar_b64']}" />
            <div class="player-info">
                <div class="trophy-text">{p['trophy']}</div>
                <div class="player-name">{p['name']}</div>
                <div class="badges">
                    <div class="rating-badge">
                        <span class="rating-label">でらっくす RATING</span>
                        <span class="rating-num">{p['rating_val']}</span>
                    </div>
                    <img class="badge-img" src="{p['course_b64']}" />
                    <img class="badge-img" src="{p['class_b64']}" />
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

        new_html  = self._section_html("NEW SONGS", new)
        best_html = self._section_html("OLD SONGS", best)

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
                background-image: url('file:///{self.bg_path}');
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
            .cover {{ width: 100%; height: 100%; object-fit: cover; }}
            .overlay {{ position: absolute; inset: 0; background: rgba(0,0,0,0.2); }}
            .kind-icon {{ position: absolute; top: 6px; left: 6px; height: 24px; }}
            .top-right {{
                position: absolute; top: 6px; right: 8px;
                color: white; font-size: 18px; font-weight: bold;
                background: rgba(0,0,0,0.5); padding: 2px 6px; border-radius: 4px;
            }}
            .bottom {{
                position: absolute; bottom: 0; left: 0; right: 0;
                background: rgba(0,0,0,0.6); padding: 6px 8px 4px;
                display: flex; flex-direction: column; gap: 2px;
            }}
            .bottom-row {{ display: flex; justify-content: space-between; align-items: flex-end; }}
            .title {{
                color: white; font-size: 22px; font-weight: bold;
                white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
            }}
            .score {{ color: #ddd; font-size: 16px; font-weight: 900; }}
            .rank-icon {{ height: 28px; flex-shrink: 0; }}
            .rating {{
                color: white; font-size: 32px; font-weight: bold;
                line-height: 1; flex-shrink: 0; margin-left: 8px;
            }}
            .header {{
                display: flex; align-items: center; gap: 16px;
                border-radius: 16px; padding: 12px 16px; margin-bottom: 12px;
                background-image: url('{p['nameplate_b64']}');
                background-size: cover; background-position: center;
                position: relative; overflow: hidden;
            }}
            .header::after {{
                content: ''; position: absolute; inset: 0;
                background: rgba(0,0,0,0.05); border-radius: 16px; z-index: 0;
            }}
            .header > * {{ position: relative; z-index: 1; }}
            .header-right {{ margin-left: auto; display: flex; flex-direction: column; align-items: flex-end; gap: 6px; }}
            .score-summary {{ display: flex; gap: 16px; }}
            .score-block {{ text-align: center; }}
            .score-num {{ color: white; font-size: 28px; font-weight: 900; text-shadow: 2px 2px 6px rgba(0,0,0,0.8); }}
            .score-label {{ color: white; font-size: 13px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.8); }}
            .score-avg {{ color: white; font-size: 16px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.8); }}
            .gen-date {{ color: white; font-size: 14px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.8); }}
            .avatar {{ width: 100px; height: 100px; border-radius: 12px; border: 3px solid white; box-shadow: 3px 3px 8px rgba(0,0,0,0.3); }}
            .player-info {{ display: flex; flex-direction: column; gap: 6px; }}
            .trophy-text {{ color: white; font-size: 14px; text-shadow: 1px 1px 3px rgba(0,0,0,0.5); }}
            .player-name {{ color: white; font-size: 28px; font-weight: 900; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); letter-spacing: 4px; }}
            .badges {{ display: flex; align-items: center; gap: 10px; }}
            .rating-badge {{ background: rgba(0,0,0,0.2); border-radius: 8px; padding: 4px 12px; display: flex; align-items: center; gap: 8px; }}
            .rating-label {{ color: #aaddff; font-size: 12px; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.8); }}
            .rating-num {{ color: white; font-size: 24px; font-weight: 900; text-shadow: 2px 2px 4px rgba(0,0,0,0.8); }}
            .badge-img {{ height: 36px; }}
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

    def _screenshot(self):
        import base64
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--window-size=1300,900")
        options.add_argument("--hide-scrollbars")
        driver = webdriver.Chrome(options=options)

        driver.get(f"file:///{os.path.abspath('rating.html')}")
        time.sleep(2)

        width  = driver.execute_script("return document.body.scrollWidth")
        height = driver.execute_script("return document.body.scrollHeight")
        driver.set_window_size(width + 20, height + 20)
        time.sleep(1)

        result = driver.execute_cdp_cmd("Page.captureScreenshot", {
            "format": "png",
            "captureBeyondViewport": True,
            "clip": {"x": 0, "y": 0, "width": width, "height": height, "scale": 1},
        })

        with open("rating.png", "wb") as f:
            f.write(base64.b64decode(result["data"]))

        driver.quit()
        print("rating.png 已產生")


# =====================
# Discord 機器人
# =====================
cred_manager = CredentialManager()

TOKEN = "MTQ5MDY2NDkwNzEwMjc0ODc0Mw.GFUSh1.xoOZ9nmkb3-YZkjSKCFjTnRRguaGL9fK1_U60I"

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)


def generate_rating_image(segaid: str, password: str, bg_path: str = "bg_vertical.jpg"):
    data      = MaimaiData()
    client    = MaimaiClient(data)

    if not client.login(segaid, password):
        raise Exception("登入失敗")

    client.fetch_player_info()
    client.fetch_scores()

    generator = MaimaiImageGenerator(client, bg_path=bg_path)
    generator.generate()


class LoginModal(discord.ui.Modal, title="maimai 登入"):
    segaid = discord.ui.TextInput(
        label="Sega ID",
        placeholder="請輸入你的 Sega ID",
        required=True
    )
    password = discord.ui.TextInput(
        label="密碼",
        placeholder="請輸入你的密碼",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        cred_manager.save(interaction.user.id, self.segaid.value, self.password.value)
        await interaction.followup.send("登入資料已儲存！可以使用 `/rating` 生成圖片了", ephemeral=True)


@tree.command(name="login", description="登入你的 maimai 帳號")
async def login(interaction: discord.Interaction):
    await interaction.response.send_modal(LoginModal())


@tree.command(name="logout", description="登出並清除你的登入資料")
async def logout(interaction: discord.Interaction):
    cred_manager.delete(interaction.user.id)
    await interaction.response.send_message("已清除你的登入資料！", ephemeral=True)


@tree.command(name="rating", description="生成你的 maimai rating 圖片")
@app_commands.describe(background="上傳自訂背景圖片（可選）")
async def rating(interaction: discord.Interaction, background: discord.Attachment = None):
    creds = cred_manager.load(interaction.user.id)
    if creds is None:
        await interaction.response.send_message("請先使用 `/login` 登入！", ephemeral=True)
        return

    await interaction.response.defer()

    if background is not None:
        bg_path = f"bg_{interaction.user.id}.jpg"
        bg_data = await background.read()
        with open(bg_path, "wb") as f:
            f.write(bg_data)
        cred_manager.save_background(interaction.user.id, bg_path)
    else:
        bg_path = cred_manager.load_background(interaction.user.id)

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: generate_rating_image(creds["segaid"], creds["password"], bg_path=bg_path)
        )
        await interaction.followup.send(file=discord.File("rating.png"))
    except Exception as e:
        await interaction.followup.send(f"發生錯誤：{e}")

@bot.event
async def on_ready():
    await tree.sync()
    print(f"機器人已上線：{bot.user}")


if __name__ == "__main__":
    bot.run(TOKEN)
