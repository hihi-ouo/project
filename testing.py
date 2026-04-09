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


driver: WebDriver = webdriver.Chrome()

path = (
    "https://www.youtube.com/"
)

driver.get(path)

wait = WebDriverWait(driver, 10)

find(By.NAME, "search_query").send_keys("folern")
find(By.XPATH, "//button[@class= 'ytSearchboxComponentSearchButton ytSearchboxComponentSearchButtonDark']").click() 
time.sleep(2)
find(By.XPATH, "//a[@id='video-title']").click()

time.sleep(8)
driver.quit()


