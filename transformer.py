import json
from bs4 import BeautifulSoup
from scraper import get_requirements
from alive_progress import alive_bar


def get_courses():
    data = None
    with open("vikelabs-store/courses.json", "r", encoding="utf8") as f:
        data = json.load(f)
    return data


def transform_data(bar):
    courses = get_courses()
    transformed_courses = {}

    for vike_course in courses:
        course_id = vike_course["__catalogCourseId"]

        hasReqs = "preAndCorequisites" in vike_course
        reqs = []
        if hasReqs:
            html_reqs = vike_course["preAndCorequisites"]
            reqs = get_requirements(
                BeautifulSoup(html_reqs, "html.parser"))

        url = "https://www.uvic.ca/calendar/undergrad/index.php#/courses/" + \
            vike_course["pid"]

        transformed_courses[course_id] = {
            "courseId": vike_course["__catalogCourseId"],
            "title": vike_course["title"],
            "pid": vike_course["pid"],
            "parsedRequirements": reqs,
            "url": url,
        }
        bar()

    return transformed_courses


def main():
    output = None
    with alive_bar(3438) as bar:
        output = transform_data(bar)

    json_output_name = "courses.json"
    with open("output/"+json_output_name, "w") as outfile:
        outfile.write(json.dumps(output))


if __name__ == "__main__":
    main()
