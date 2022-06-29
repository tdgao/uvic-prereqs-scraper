from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from bs4 import BeautifulSoup
import copy
import json


#object of Options class, passing headless parameter
c = Options()
c.add_argument('--headless')
s = Service('chromedriver-v103.exe')
browser = webdriver.Chrome(service=s, options=c)
browser.set_window_size(1120, 550)

program_url = 'https://www.uvic.ca/calendar/undergrad/index.php#/programs/S1gtLTm0ME'
browser.get(program_url)

## gets pre reqs container and adds wait time for content to load
element = WebDriverWait(browser, 5).until(
    EC.presence_of_element_located((By.CLASS_NAME, "rules-wrapper"))
)

## using BeautifulSoup to parse html 
soup = BeautifulSoup(browser.page_source, 'html.parser')
container = soup.select(".rules-wrapper")[0]



"""
# ul denotes new requirement (complete 1 of, complete all of)
# ul's each li denotes requirement item
for ul
    look into each li
    if li has ul child
        remove ul and keep
    log li.text

    repeat for ul
"""

def top_ul(tag):
    return len(tag.find_parents("ul")) == 0 and tag.name == "ul"

def get_requirements(ul):
    requirements = []
    
    # all_top_ul = ul.find_all(top_ul)
    # print(len(ul.find_parents("ul")) == 0)

    for li in ul.find_all(["li", "div"], recursive=False):
        nested_ul = li.find("ul")
        if (nested_ul):
            li_title = copy.copy(li) # title (complete all of the following, complete all of, compete 1 of)
            li_title.find("ul").decompose()

            nested_req = {
                li_title.get_text(): get_requirements(nested_ul)
            }
            requirements.append(nested_req)
        else:
            requirements.append(li.get_text())

    return requirements



all_ul = container.find_all(top_ul) # root ul of all years from program
for ul in all_ul:
    requirements = get_requirements(ul) 
    print( json.dumps(requirements,indent=2) )


browser.quit()