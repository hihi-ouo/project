from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time


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

time.sleep(8)

driver.quit()