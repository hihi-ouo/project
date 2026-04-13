import discord
from discord import app_commands
import asyncio
import os

from credentials import CredentialManager
from data import MaimaiData
from client import MaimaiClient
from image_generator import MaimaiImageGenerator
from dotenv import load_dotenv


# =====================
# Discord 機器人
# =====================
cred_manager = CredentialManager()
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

#建立機器人
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)


# 把前幾個檔案的class合併到這裡開始執行
def generate_rating_image(segaid: str, password: str, bg_path: str = "bg_vertical.jpg"):
    data   = MaimaiData()
    client = MaimaiClient(data)

    # 登入maimai DX net
    if not client.login(segaid, password):
        raise Exception("登入失敗")

    client.fetch_player_info() # 抓取玩家基本資料
    client.fetch_scores() # 抓取玩家成績

    # 生成圖片，同時設定背景圖片為使用者指定的圖片(若沒有則是預設圖片)
    generator = MaimaiImageGenerator(client, bg_path=bg_path) 
    generator.generate()


class LoginModal(discord.ui.Modal, title="maimai 登入"):
    # 使用disocord內建的ui，接受使用者輸入的帳號和密碼
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
        cred_manager.save(interaction.user.id, self.segaid.value, self.password.value) # 將使用者的帳密加密後儲存，使得每次詢問不用重新登入
        await interaction.followup.send("登入資料已儲存！可以使用 `/rating` 生成圖片了", ephemeral=True)


# @tree.command是一個裝飾器，用來定義一個新的指令，name是指令名稱，description是指令描述
# 這邊的login, logout都不會太耗時，所以可以直接response
@tree.command(name="login", description="登入你的 maimai 帳號")
async def login(interaction: discord.Interaction):
    await interaction.response.send_modal(LoginModal()) # send_modal把視窗(ui)彈出，搭配前面的discord.ui.TextInput接收輸入


@tree.command(name="logout", description="登出並清除你的登入資料")
async def logout(interaction: discord.Interaction):
    cred_manager.delete(interaction.user.id) # 刪除儲存資料
    await interaction.response.send_message("已清除你的登入資料！", ephemeral=True)


@tree.command(name="rating", description="生成你的 maimai rating 圖片")
@app_commands.describe(background="上傳自訂背景圖片（可選）") # 增加參數(我是增加background自訂的選項)
async def rating(interaction: discord.Interaction, background: discord.Attachment = None):
    creds = cred_manager.load(interaction.user.id)
    # 確認是否已登入，沒有則優先要求使用者登入
    if creds is None:
        await interaction.response.send_message("請先使用 `/login` 登入！", ephemeral=True)
        return

    # 由於discord機器人的邏輯是收到指令後須在3秒內回應，所以必須使用defer()告知discord機器人正在處理
    await interaction.response.defer() 

    # 存入background圖片並使用，否則就是拿使用者先前設定過的圖片或是預設圖片
    if background is not None:
        bg_path = f"bg_{interaction.user.id}.jpg"
        bg_data = await background.read()
        with open(bg_path, "wb") as f:
            f.write(bg_data)
        cred_manager.save_background(interaction.user.id, bg_path)
    else:
        bg_path = cred_manager.load_background(interaction.user.id)

    try:
        loop = asyncio.get_event_loop() # 跑底下的這個事件循環
        await loop.run_in_executor(
            None,
            lambda: generate_rating_image(creds["segaid"], creds["password"], bg_path=bg_path) # 比較耗時，所以丟到背景執行，等待他跑完就會到下行回傳檔案
        )
        await interaction.followup.send(file=discord.File("rating.png")) # 
    except Exception as e:
        await interaction.followup.send(f"發生錯誤：{e}")


@bot.event
async def on_ready(): # 判斷是否連上discord，有的話就會執行下去
    await tree.sync()
    print(f"機器人已上線：{bot.user}")


# 主執行點，也就是說要執行機器人只需跑bot.py這個程式檔即可，其他的檔案都寫成class並呼叫進來了
if __name__ == "__main__":
    bot.run(TOKEN)
