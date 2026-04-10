from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from datetime import date
from client import MaimaiClient
from constants import DIFF_COLORS
import base64
import time
import os


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
        kind_icon    = p["dx_icon_b64"] if kind == "DX" else p["std_icon_b64"]
        rank_icon    = p["rank_icon_b64"].get(score_level)
        image_url    = f"https://shama.dxrating.net/images/cover/v2/{image_name}.jpg"
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
