def top_ul(tag):
    return len(tag.find_parents("ul")) == 0 and tag.name == "ul"


def get_page_h2(soup):
    full_title_h2 = soup.select("#__KUALI_TLP h2")
    if (len(full_title_h2) > 0):
        return full_title_h2[0].get_text()


# removes all url params (everything after #)
def clean_url(url):
    return url.split("?")[0]
