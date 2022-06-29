from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup
browser = webdriver.Chrome(executable_path=r"C:\Users\Truman\Desktop\code for fun\UVic-pre-reqs-scraper\chromedriver.exe")
browser.set_window_size(1120, 550)
browser.get('https://www.uvic.ca/calendar/undergrad/index.php#/programs/S1gtLTm0ME')

## gets pre reqs container
# element = WebDriverWait(browser, 5).until(
#    EC.presence_of_element_located((By.CLASS_NAME, "rules-wrapper"))
# )

# data = element.get_attribute('data-blabla')
# print(element.text)

## using BeautifulSoup to parse html ##

soup = BeautifulSoup(browser.page_source, 'html.parser')
print(soup.select(".rules-wrapper")[0].get_text())

# use ul and li to put pre req into into object, check 'complete'


browser.quit()