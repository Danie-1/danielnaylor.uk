import functools
import re

from bs4 import BeautifulSoup, Tag
from flask import render_template

from generate_webpage import get_course_from_alias


@functools.cache
def fix_paginated_html(course: str, content: str) -> str:
    soup = BeautifulSoup(content, features="html.parser")

    head = soup.find("head")
    assert isinstance(head, Tag)
    head.find("title").decompose()

    body = soup.find("body")
    assert isinstance(body, Tag)

    crosslinks = soup.find("div", {"class": "crosslinks"})
    include_navigation = crosslinks is not None
    if include_navigation:
        match_previous = re.search(r'<a href="([^"]*)">prev</a>', str(crosslinks))
        if match_previous:
            has_previous = True
            previous_link = match_previous.group(1)
        else:
            has_previous = False
            previous_link = None
        match_next = re.search(r'<a href="([^"]*)">next</a>', str(crosslinks))
        if match_next:
            has_next = True
            next_link = match_next.group(1)
        else:
            has_next = False
            next_link = None
    else:
        has_previous = None
        previous_link = None
        has_next = None
        next_link = None

        for toclink in soup.find_all("span", {"class": "sectionToc"}):
            if toclink.text == "Index":
                toclink.decompose()

        for likesection_toc in soup.find_all("span", {"class": "likesectionToc"}):
            if likesection_toc.text == "Index":
                likesection_toc.previous_sibling.decompose()
            likesection_toc["class"] = "sectionToc"

    while crosslinks := soup.find("div", {"class": "crosslinks"}):
        crosslinks.decompose()

    # for maybe_delete in soup.select("p.noindent"):
    #     if maybe_delete.decode_contents().strip() == "˙":
    #         maybe_delete.decompose()

    return render_template(
        "notes_paginated.html",
        content=body.decode_contents(),
        head=head.decode_contents(),
        title=f"{get_course_from_alias(course).course_name} Notes",
        course_code=course,
        include_navigation=include_navigation,
        has_previous=has_previous,
        previous_link=previous_link,
        has_next=has_next,
        next_link=next_link,
    )
