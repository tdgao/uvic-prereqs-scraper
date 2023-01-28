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


def get_page_source(url):
    # object of Options class, passing headless parameter
    c = Options()
    c.add_argument("--headless")
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
    c.add_argument(f"user-agent={user_agent}")

    s = Service("drivers/chromedriver-v109.exe")
    browser = webdriver.Chrome(service=s, options=c)
    # browser.set_window_size(1120, 550)

    browser.get(url)

    try:
        # program waits until pre reqs container content is loaded
        element = WebDriverWait(browser, 10).until(
            # class name of description h3 # id is container of loaded content
            EC.presence_of_element_located((By.CLASS_NAME, "rules-wrapper"))
        )
    except:
        print("no rules wrapper after 10 seconds")

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


def top_ul(tag):
    return len(tag.find_parents("ul")) == 0 and tag.name == "ul"


def get_page_h2(soup):
    full_title_h2 = soup.select("#__KUALI_TLP h2")
    if (len(full_title_h2) > 0):
        return full_title_h2[0].get_text()


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
    print("Fetching course:", course_url)
    soup = get_page_source(course_url)
    container = get_prereq_container(soup=soup)

    requirements = get_requirements(container.find(top_ul))

    # gets main title e.g. "MATH102 - Calculus for Students in the Social and Biological Sciences"
    course_title = get_page_h2(soup)

    course_id = course_title.split(" - ")[0]
    short_description = course_title.split(" - ")[1]

    return {
        course_id: {
            "courseId": course_id,
            "shortDescription": short_description,
            "prerequisites": requirements,
            "url": course_url
        }
    }


def get_program_courses(courses_container):
    courses = {}

    # get all course name and urls, then requirements
    for i, course in enumerate(courses_container.find_all('a')):
        # course_name = course.get_text()
        course_url = "https://www.uvic.ca/calendar/undergrad/index.php" + \
            str(course['href'])
        # print(course_name, course_url)
        get_course_requirements(course_url)

        # if (i > 3): break #for testing

    # print(json.dumps(program_courses, indent=2))
    return courses


def get_program_requirements(program_url):
    soup = get_page_source(program_url)
    container = get_prereq_container(program_url, soup=soup)
    program_requirements = {}

    program_name = get_page_h2(soup=soup)
    # root ul of all years from program
    all_year_ul = container.find_all(top_ul)

    for i, year_ul in enumerate(all_year_ul, 1):
        requirements = get_requirements(year_ul)
        year = "year-" + str(i)
        program_requirements[year] = requirements

    return {
        program_name: program_requirements
    }


def main():
    program_url = 'https://www.uvic.ca/calendar/undergrad/index.php#/programs/S1gtLTm0ME'
    program_requirements = get_program_requirements(program_url)

    # Writing to programs.json
    json_output_name = "programs.json"
    with open("output/"+json_output_name, "w") as outfile:
        outfile.write(json.dumps(program_requirements))

    course_url = "https://www.uvic.ca/calendar/undergrad/index.php#/courses/HySJ0P67N"
    course_requirements = get_course_requirements(course_url)

    # Writing to courses.json
    json_output_name = "courses.json"
    with open("output/"+json_output_name, "w") as outfile:
        outfile.write(json.dumps(course_requirements))

    print("End of scraping.")


if __name__ == "__main__":
    main()
