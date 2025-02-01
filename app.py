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
        return Response(
            re.sub(r"body {([^}]*)}", r"\1", f"#content {{ {file.read_text()} }}"),
            mimetype="text/css",
        )
    if not html_file.endswith("html"):
        return send_file(file)
    content = file.read_text()
    # return render_template("notes_paginated.html", content=content)
    soup = BeautifulSoup(content, features="html.parser")
    head = soup.find("head")
    assert isinstance(head, Tag)
    head.find("title").decompose()
    body = soup.find("body")
    assert isinstance(body, Tag)
    return render_template(
        "notes_paginated.html",
        content=body.decode_contents(),
        head=head.decode_contents(),
        title=f"{get_course_from_alias(course).course_name} Notes",
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
