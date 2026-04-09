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
from bisect import bisect_right
import requests
import time
import json
import os


def find(by, value):
    return wait.until(EC.element_to_be_clickable((by, value)))

if not os.path.exists("dxdata.json"):
    response = requests.get("https://raw.githubusercontent.com/gekichumai/dxrating/main/packages/dxdata/dxdata.json")
    dx_data = response.json()
    with open("dxdata.json", "w", encoding="utf-8") as f:
        json.dump(dx_data, f, ensure_ascii=False, indent=2)


with open("dxdata.json", "r", encoding="utf-8") as f:
    dx_data = json.load(f)


level_map = {}
for song in dx_data["songs"]:
    title = song["title"]
    new_song = song["isNew"]
    for sheet in song["sheets"]:
        if sheet["type"] == "dx":
            chart_type = "DX"
        else:
            chart_type = "STANDARD"
        difficulty = sheet["difficulty"]
        level_map[(title, chart_type, difficulty)] = [sheet["internalLevelValue"], new_song]


segaid = input("Please enter your sega id    ")
password = input("Please enter your password    ")



path = (
    "https://lng-tgk-aime-gw.am-all.net/common_auth/login?"
    "site_id=maimaidxex&redirect_url=https://maimaidx-eng.com/"
    "maimai-mobile/&back_url=https://maimai.sega.com/"

)


driver: WebDriver = webdriver.Chrome()
driver.get(path)
wait = WebDriverWait(driver, 10)


find(By.XPATH, "//label[@class='c-form__label--bg agree']").click()
find(By.XPATH, "//span[@class='c-button--openid--segaId']").click()
find(By.NAME, "sid").send_keys(segaid)
find(By.NAME, "password").send_keys(password)
find(By.XPATH, "//button[@class='c-button--login js-agreeSubmit']").click()



selenium_cookies = driver.get_cookies()
driver.quit()


session = requests.Session()
for cookie in selenium_cookies:
    session.cookies.set(cookie['name'], cookie['value'])

headers = {"User-Agent": "hihiouo"}
DIFFICULTIES = [[2, "expert"], [3, "master"], [4, "remaster"]]
results = []

for difficulties in DIFFICULTIES:
 
    response = session.get(f"https://maimaidx-eng.com/maimai-mobile/record/musicGenre/search/?genre=99&diff={difficulties[0]}", headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")   


    for row in soup.select(".m_15"):
        if "screw_block" in row.get("class"):
            continue

        name = row.select_one(".music_name_block")
        score = row.select_one(".music_score_block.w_112")
        kind = row.select_one(".music_kind_icon")

        if score:

            if "music_dx" in kind.get("src"):
                chart_type = "DX"
            else:
                chart_type = "STANDARD" 
            
            score_text = score.get_text(strip=True)

            results.append({
                "title": name.get_text(strip=True),
                "score": float(score_text[:-1]),
                "kind" : chart_type,
                "difficulty": difficulties[1]
            })


score_coefficient = [[80, 0.136], [90, 0.152], [94, 0.168], [97, 0.2], [98, 0.203], [99, 0.208], [99.5, 0.211], [100, 0.216], [100.5, 0.224]]
best_35, new_15 = [], []


for r in results:

    level, isnew = level_map[(r["title"], r["kind"], r["difficulty"])][0], level_map[(r["title"], r["kind"], r["difficulty"])][1]
    idx = bisect_right(score_coefficient, r["score"], key = lambda x:x[0])

    if idx != 0:
        coefficient = score_coefficient[idx-1][1]
    else:
        coefficient = 0

    rating = r["score"] * coefficient * level
    if isnew:
        new_15.append([r["title"], r["score"], r["difficulty"], level, int(rating)])
    else:
        best_35.append([r["title"], r["score"], r["difficulty"], level, int(rating)])


best_35.sort(key = lambda x:x[4], reverse = True)
new_15.sort(key = lambda x:x[4], reverse = True)

print("----")
print("old songs")
print("----")

for b in best_35[:80]:
    print(*b)

print("----")
print("new songs")
print("----")

for n in new_15:
    print(*n)

