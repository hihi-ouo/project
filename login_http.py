import requests
from bs4 import BeautifulSoup

LOGIN_URL = (
    "https://lng-tgk-aime-gw.am-all.net/common_auth/login"
    "?site_id=maimaidxex"
    "&redirect_url=https://maimaidx-eng.com/maimai-mobile/"
    "&back_url=https://maimai.sega.com/"
)

SEGA_ID = input("請輸入你的SEGA_ID")
PASSWORD = input("請輸入你的密碼")

session = requests.Session()
session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
})

# 第一步：取得登入頁面（獲取 CSRF token 等隱藏欄位）
resp = session.get(LOGIN_URL)
soup = BeautifulSoup(resp.text, "html.parser")

# 收集所有隱藏 input 欄位
form_data = {}
for tag in soup.find_all("input", type="hidden"):
    if tag.get("name"):
        form_data[tag["name"]] = tag.get("value", "")

# 加入帳號密碼
form_data["sid"] = SEGA_ID       # SEGA ID 欄位名稱（可能需依實際 HTML 調整）
form_data["password"] = PASSWORD  # 密碼欄位名稱
form_data["retention"] = "1"
form_data["agree"] = "on"      # 同意服務條款

# 第二步：POST 登入表單
login_resp = session.post(LOGIN_URL, data=form_data, allow_redirects=True)

print("最終網址：", login_resp.url)

# 第三步：確認是否成功跳轉到 maimai home
if "maimaidx-eng.com/maimai-mobile/home" in login_resp.url:
    print("✅ 登入成功！")
else:
#    print("❌ 登入失敗，目前頁面：", login_resp.url)
    print("❌ 登入失敗")
    print("回應內容：", login_resp.text[:500])

# 第四步：使用同一個 session 存取其他頁面
#home = session.get("https://maimaidx-eng.com/maimai-mobile/home/")
#print(home.status_code, home.url)