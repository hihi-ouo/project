from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from data import MaimaiData
from constants import HEADERS, LOGIN_URL, RANK_ICONS
import requests
import base64
import time


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
        avatar_url = imgs[0].get("src")
        course_url = next(i.get("src") for i in imgs if "course" in i.get("src", ""))
        class_url  = next(i.get("src") for i in imgs if "class_rank" in i.get("src", ""))

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
            if level is None:
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
