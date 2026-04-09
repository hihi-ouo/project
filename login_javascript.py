from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import getpass
import time

LOGIN_URL = (
    "https://lng-tgk-aime-gw.am-all.net/common_auth/login"
    "?site_id=maimaidxex"
    "&redirect_url=https://maimaidx-eng.com/maimai-mobile/"
    "&back_url=https://maimai.sega.com/"
)

SEGA_ID = input("請輸入 SEGA ID：")
PASSWORD = input("請輸入密碼（輸入時不會顯示）：")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get(LOGIN_URL)

wait = WebDriverWait(driver, 10)
wait.until(EC.presence_of_element_located((By.ID, "sid")))

# 填入帳號密碼
driver.execute_script("""
var sid = document.getElementById('sid');
sid.value = arguments[0];
sid.dispatchEvent(new Event('input', {bubbles: true}));
sid.dispatchEvent(new Event('change', {bubbles: true}));

var pwd = document.getElementById('password');
pwd.value = arguments[1];
pwd.dispatchEvent(new Event('input', {bubbles: true}));
pwd.dispatchEvent(new Event('change', {bubbles: true}));
""", SEGA_ID, PASSWORD)

# 勾選條款並觸發完整事件
driver.execute_script("""
document.querySelectorAll('.js-agree').forEach(cb => {
    cb.checked = true;
    cb.dispatchEvent(new MouseEvent('click', {bubbles: true}));
    cb.dispatchEvent(new Event('change', {bubbles: true}));
});
""")

time.sleep(1)

# 強制移除 disabled 並點擊登入按鈕
driver.execute_script("""
var btn = document.querySelector('button.c-button--login');
btn.disabled = false;
btn.removeAttribute('disabled');
btn.click();
""")

# 等待跳轉
time.sleep(3)

print("最終網址：", driver.current_url)

if "maimaidx-eng.com/maimai-mobile/home" in driver.current_url:
    print("✅ 登入成功！")
else:
    print("❌ 登入失敗，目前在：", driver.current_url)