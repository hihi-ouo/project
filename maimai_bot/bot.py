import discord
from discord import app_commands
import asyncio

from credentials import CredentialManager
from data import MaimaiData
from client import MaimaiClient
from image_generator import MaimaiImageGenerator


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
    data   = MaimaiData()
    client = MaimaiClient(data)

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
