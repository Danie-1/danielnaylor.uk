import os
from pathlib import Path
import re

from dotenv import load_dotenv
from flask import Flask, Response, abort, redirect, render_template, send_file
from flask_bootstrap import Bootstrap5
from bs4 import BeautifulSoup, Tag

from generate_webpage import (
    BASE_FOLDER,
    get_course_from_alias,
    get_course_from_course_code,
    get_years,
    part_to_year_number,
    term_name_to_number,
)


app = Flask(__name__)
Bootstrap5(app)


def html_url_to_file_url(year: str, term: str, course: str) -> Path:
    return BASE_FOLDER / part_to_year_number(year) / term_name_to_number(term) / course


@app.route("/notes/<year>/<term>/<course>/<pdf_file>.pdf")
def notes_pdf(year: str, term: str, course: str, pdf_file: str):
    return send_file(html_url_to_file_url(year, term, course) / f"{pdf_file}.pdf")


@app.route("/notes/<year>/<term>/<course>/<path:html_file>")
def notes_html(year: str, term: str, course: str, html_file: str):
    if html_file == f"{course}.html":
        html_file = f"{course}_final.html"
    return send_file(html_url_to_file_url(year, term, course) / f"HTML/{html_file}")


@app.route("/notes/<year>/<term>/<course>/HTML/<path:html_file>")
def notes_html_paginated(year: str, term: str, course: str, html_file: str):
    file = html_url_to_file_url(year, term, course) / f"HTML_paginated/{html_file}"
    if html_file.endswith("css"):
        replacements = [
            (r"body {([^}]*)}", ""),
            (r"@media \(prefers-color-scheme: dark\) {[^}]*}", ''),
        ]
        css = f"#pagecontent {{ {file.read_text()} }}"
        for pattern, replacement in replacements:
            css = re.sub(pattern, replacement, css)
        return Response(css, mimetype="text/css")
    if not html_file.endswith("html"):
        return send_file(file)
    content = file.read_text()
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

    while (crosslinks := soup.find("div", {"class": "crosslinks"})):
        crosslinks.decompose()

    for maybe_delete in soup.select("p.noindent"):
        if maybe_delete.decode_contents().strip() == "˙":
            maybe_delete.decompose()

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


@app.route("/<alias>")
def course_redirect(alias: str):
    if not (course := get_course_from_alias(alias)):
        return abort(404)
    return redirect(course.pdf_url())


@app.route("/<alias>.html")
def course_html_redirect(alias: str):
    if not (course := get_course_from_alias(alias)):
        return abort(404)
    return redirect(course.html_url())


@app.route("/notes/<course_code>.apkg")
def flashcards(course_code: str):
    if not get_course_from_course_code(course_code):
        return abort(404)
    return send_file(BASE_FOLDER / f"{course_code.upper()}.apkg")


@app.route("/notes/")
def notes_home():
    term_list = [term for year in get_years() for term in year.get_terms()]
    return render_template("notes_home.html", terms=term_list)


# @app.route("/blog/")
# def blog_home():
#     return render_template("blog_home.html")


# @app.route("/blog/<path:blog_path>")
# def blog(blog_path: str):
#     return redirect(url_for("blog_home"))


@app.route("/")
def home():
    return render_template("home.html")


if __name__ == "__main__":
    load_dotenv()
    debug = os.environ.get("FLASK_DEBUG") is not None
    app.run(port=5005, debug=debug)
