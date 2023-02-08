import random
import time
from pkg_resources import require
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from bs4 import BeautifulSoup
import copy
import json
import os

from utils import clean_url, get_page_h2, top_ul


"""
ul denotes new requirement (complete 1 of, complete all of)
ul's each li denotes requirement item
for ul
    look into each li
    if li has ul child
        remove ul and keep
    log li.text

    repeat for ul
"""


def get_page_source(url, load_element=".rules-wrapper"):
    # time.sleep(random.randrange(2, 10, 1))
    # object of Options class, passing headless parameter
    options = Options()
    # following 3 lines allow for headless
    options.add_argument("--headless")
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
    options.add_argument(f"user-agent={user_agent}")
    # disable message:"DevTools listening on ws...
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    # ensure version matches installed chrome version
    s = Service("drivers/chromedriver-v109.exe")

    browser = webdriver.Chrome(service=s, options=options)
    print("Running webdriver")
    # browser.set_window_size(1120, 550)
    browser.get(url)

    try:
        # program waits until specific element is loaded
        element = WebDriverWait(browser, 10).until(
            # class name of description h3 # id is container of loaded content
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, load_element))
        )

    except:
        print("no element with selector: %s after 10 seconds" % load_element)

    # using BeautifulSoup to parse html
    soup = BeautifulSoup(browser.page_source, "html.parser")
    browser.quit()

    return soup


def get_prereq_container(url=None, soup=None):
    if (url == None and soup == None):
        print("Cant get prereqs: no soup or URL")
        return
    if (soup == None):
        soup = get_page_source(url)  # if pass in soup, will not run webdriver

    container = BeautifulSoup("")
    if (len(soup.select(".rules-wrapper")) > 0):  # list is not empty
        container = soup.select(".rules-wrapper")[0]
    else:
        print("empty prereq container")
    return container


def get_requirements(ul):
    if (ul == None):
        return []
    requirements = []

    # all_top_ul = ul.find_all(top_ul)
    # print(len(ul.find_parents("ul")) == 0)

    for li in ul.find_all(["li", "div"], recursive=False):
        nested_ul = li.find("ul")
        if (nested_ul):
            # title (complete all of the following, complete all of, compete 1 of)
            li_title = copy.copy(li)
            li_title.find("ul").decompose()

            nested_req = {
                li_title.get_text(): get_requirements(nested_ul)
            }
            requirements.append(nested_req)
        else:
            if (li):  # if req has link, will return linked text (BIO123 instead of BIO123 - some description)
                if (li.find('a')):
                    requirements.append(li.find('a').get_text())
                else:
                    requirements.append(li.get_text())

    return requirements


def get_course_requirements(course_url):
    clean_url(course_url)
    print("\nScraping course:", course_url)
    soup = get_page_source(course_url)
    container = get_prereq_container(soup=soup)

    requirements = get_requirements(container.find(top_ul))

    # gets main title e.g. "MATH102 - Calculus for Students in the Social and Biological Sciences"
    course_title = get_page_h2(soup)

    course_id = course_title.split(" - ")[0]
    short_description = course_title.split(" - ")[1]

    print("Scraped:", course_id)

    return {
        course_id: {
            "courseId": course_id,
            "shortDescription": short_description,
            "prerequisites": requirements,
            "url": course_url
        }
    }


def get_program_requirements(program_url):
    clean_url(program_url)
    print("\nScraping program:", program_url)

    soup = get_page_source(program_url)
    rules_wrapper = get_prereq_container(program_url, soup=soup)
    program_requirements = {}

    program_title = get_page_h2(soup=soup)
    # root ul of all years from program
    all_year_ul = rules_wrapper.find_all(top_ul)

    for i, year_ul in enumerate(all_year_ul, 1):
        requirements = get_requirements(year_ul)
        year = "year-" + str(i)
        program_requirements[year] = requirements

    print("Scraped:", program_title)

    return {
        program_title: {
            "programId": program_title,
            "url": program_url,
            "requirements": program_requirements,
            "htmlRequirements": str(rules_wrapper),
        }
    }


def get_all_program_reqs(testing=False):
    # get all program URLs
    # run through URLs and populate object with requirements
    # do the same with courses
    # get all course name and urls, then requirements
    all_program_reqs = {}

    programs_url = "https://www.uvic.ca/calendar/undergrad/index.php#/programs"
    programs_soup = get_page_source(programs_url, load_element="#__KUALI_TLP")
    programs_container = programs_soup.select("#__KUALI_TLP ul")[0]
    for i, program in enumerate(programs_container.find_all('a')):
        # course_name = course.get_text()
        program_url = "https://www.uvic.ca/calendar/undergrad/index.php" + \
            str(program['href'])
        # print(course_name, course_url)
        program_reqs = get_program_requirements(program_url)
        all_program_reqs = {**all_program_reqs, **program_reqs}

        if testing and i > 3:  # end early for testing
            break

    return all_program_reqs


def get_all_course_reqs(testing=False):
    all_course_reqs = {}
    # get subject list container, get all a tags from subject list,
    # for each subject site, scrape all course prereqs
    course_url = "https://www.uvic.ca/calendar/undergrad/index.php#/courses"
    subjects_container = get_page_source(
        course_url, load_element="#subjects-list-nav").select("#subjects-list-nav")[0]
    for i, subject in enumerate(subjects_container.find_all('a')):
        subject_url = "https://www.uvic.ca/calendar/undergrad/index.php" + \
            str(subject['href'])
        courses_container = get_page_source(
            subject_url, load_element="#__KUALI_TLP ul").select("#__KUALI_TLP")[0]

        if testing and i > 2:  # end early for testing
            break

        for i, course in enumerate(courses_container.find_all('a')):
            course_url = "https://www.uvic.ca/calendar/undergrad/index.php" + \
                str(course['href'])
            course_reqs = get_course_requirements(course_url)
            all_course_reqs = {**all_course_reqs, **course_reqs}

            if testing and i > 2:  # end early for testing
                break

    return all_course_reqs


def main():

    ### GET ALL PROGRAM REQS
    # all_program_reqs = get_all_program_reqs()

    # # Writing to programs.json
    # json_output_name = "programs.json"
    # with open("output/"+json_output_name, "w") as outfile:
    #     outfile.write(json.dumps(all_program_reqs))


    ### GET SOME PROGRAM REQS
    program_urls = [
        "https://www.uvic.ca/calendar/undergrad/index.php#/programs/SkYVTmCzE",
        "https://www.uvic.ca/calendar/undergrad/index.php#/programs/ByRI6X0z4",
        "https://www.uvic.ca/calendar/undergrad/index.php#/programs/SJKVp7AME",
        "https://www.uvic.ca/calendar/undergrad/index.php#/programs/B1gkKa70z4",
        "https://www.uvic.ca/calendar/undergrad/index.php#/programs/S1l9V6mCfV",
        "https://www.uvic.ca/calendar/undergrad/index.php#/programs/HkCK67AGV",
    ]
    program_reqs = {}
    for url in program_urls:
        cur = get_program_requirements(url)
        program_reqs = {**program_reqs, **cur}

    # Writing to programs.json
    json_output_name = "temp.json"
    with open("output/"+json_output_name, "w") as outfile:
        outfile.write(json.dumps(program_reqs))


    print("\nEnd of scraping 😁😁😁")


if __name__ == "__main__":
    main()
