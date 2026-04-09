from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

FONT = "C:/Windows/Fonts/YuGothR.ttc"
CARD_SIZE = (240, 240)
COLS = 5
GAP = 8
BG_COLOR = (255, 20, 147)  # 粉色背景

def make_card(title, score, level, rating, image_name, chart_type):
    url = f"https://shama.dxrating.net/images/cover/v2/{image_name}.jpg"
    cover = Image.open(BytesIO(requests.get(url).content)).convert("RGBA")
    cover = cover.resize(CARD_SIZE, Image.LANCZOS)

    overlay = Image.new("RGBA", CARD_SIZE, (0, 0, 0, 100))
    cover = Image.alpha_composite(cover, overlay)

    draw = ImageDraw.Draw(cover)
    font_small = ImageFont.truetype(FONT, 18)
    font_large = ImageFont.truetype(FONT, 32)

    draw.text((CARD_SIZE[0] - 6, 5), str(level), font=font_small, fill="white", anchor="ra")
    draw.text((5, CARD_SIZE[1] - 50), title[:10], font=font_small, fill="white")
    draw.text((CARD_SIZE[0] - 6, CARD_SIZE[1] - 40), str(rating), font=font_large, fill="white", anchor="ra")

    return cover.convert("RGB")


def make_grid(songs):
    rows = (len(songs) + COLS - 1) // COLS
    W = COLS * CARD_SIZE[0] + (COLS + 1) * GAP
    H = rows * CARD_SIZE[1] + (rows + 1) * GAP

    canvas = Image.new("RGB", (W, H), BG_COLOR)

    for i, song in enumerate(songs):
        card = make_card(**song)
        col = i % COLS
        row = i // COLS
        x = GAP + col * (CARD_SIZE[0] + GAP)
        y = GAP + row * (CARD_SIZE[1] + GAP)
        canvas.paste(card, (x, y))

    canvas.save("test_grid.png")
    print("格子圖已存成 test_grid.png")


# 測試用假資料，同一首歌重複 10 張看排版
test_songs = [
    {
        "title": "テトリス",
        "score": 100.3623,
        "level": 13.7,
        "rating": 296,
        "image_name": "c9d69620376431713e871dc5f95ec50b6789ae3cc13477fec791b1687eb290fb",
        "chart_type": "DX"
    }
] * 10

make_grid(test_songs)