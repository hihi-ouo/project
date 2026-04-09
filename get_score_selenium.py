from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import requests

options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

def find(by, value):
    return wait.until(EC.element_to_be_clickable((by, value)))

segaid = input("Please enter your sega id    ")
password = input("Please enter your password    ")

driver: WebDriver = webdriver.Chrome()


path = (
    "https://lng-tgk-aime-gw.am-all.net/common_auth/login?"
    "site_id=maimaidxex&redirect_url=https://maimaidx-eng.com/"
    "maimai-mobile/&back_url=https://maimai.sega.com/"

)

driver.get(path)

wait = WebDriverWait(driver, 10)


find(By.XPATH, "//label[@class='c-form__label--bg agree']").click()
find(By.XPATH, "//span[@class='c-button--openid--segaId']").click()
find(By.NAME, "sid").send_keys(segaid)
find(By.NAME, "password").send_keys(password)
find(By.XPATH, "//button[@class='c-button--login js-agreeSubmit']").click()
find(By.CSS_SELECTOR, 'a[href="https://maimaidx-eng.com/maimai-mobile/record/"][class="d_ib col4 p_4"]').click()
find(By.CSS_SELECTOR, 'a[href="https://maimaidx-eng.com/maimai-mobile/record/musicGenre/"][class="p_r d_ib"]').click()
find(By.CSS_SELECTOR, 'button[value="3"][class="p_r m_2 f_0"]').click()

time.sleep(2)

rows = driver.find_elements(By.CSS_SELECTOR, ".m_15")
print(f"找到 {len(rows)} 個元素")



results = []
current_genre = ""

for row in rows:
    classes = row.get_attribute("class")
    if "screw_block" in classes:
        current_genre = row.text.strip()
    
    try:
        name = row.find_element(By.CSS_SELECTOR, ".music_name_block")
        score = row.find_element(By.CSS_SELECTOR, ".music_score_block.w_112")
        results.append(f"{current_genre}\t{name.text.strip()}\t{score.text.strip()}")
    except:
        pass

for r in results:
    print(r)



driver.quit()















'''
selenium_cookies = driver.get_cookies()
driver.quit()

for cookie in selenium_cookies:
    print(cookie)

session = requests.Session()
for cookie in selenium_cookies:
    session.cookies.set(cookie['name'], cookie['value'])

headers = {
    "User-Agent": "Mozilla/5.0"
}

# 抓 MASTER 成績
response = session.get(
    "https://maimaidx-eng.com/maimai-mobile/record/musicGenre/search/?genre=99&diff=3",
    headers=headers
)

soup = BeautifulSoup(response.text, "html.parser")

results = []
current_genre = ""

for row in soup.select(".m_15"):
    if "screw_block" in row.get("class", []):
        current_genre = row.get_text(strip=True)

    name = row.select_one(".music_name_block")
    score = row.select_one(".music_score_block.w_112")

    if name and score:
        results.append({
            "genre": current_genre,
            "title": name.get_text(strip=True),
            "score": score.get_text(strip=True)
        })

for r in results:
    print(f"{r['genre']}\t{r['title']}\t{r['score']}")

'''