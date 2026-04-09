import discord
from discord.ext import commands
from discord import app_commands

TOKEN = "MTQ5MDY2NDkwNzEwMjc0ODc0Mw.GPXsr5.6_ZfwpLxc0RuZuZ56Xc-RugcpINLo7vVur_XdU"

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    await tree.sync()
    print(f"機器人已上線：{client.user}")

@tree.command(name="rating", description="生成你的maimai rating圖片")
async def rating(interaction: discord.Interaction, sega_id: str, password: str):
    await interaction.response.defer()  # 告訴 Discord 需要等一下
    
    # 這裡呼叫你的主程式邏輯
    # ...生成圖片...
    
    await interaction.followup.send(file=discord.File("rating.png"))

client.run(TOKEN)