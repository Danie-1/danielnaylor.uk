import os
import re
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, Response, abort, redirect, render_template, send_file
from flask_bootstrap import Bootstrap5

from generate_webpage import (BASE_FOLDER, get_course_from_alias,
                              get_course_from_course_code, get_years,
                              part_to_year_number, term_name_to_number)
from html_fixing import fix_paginated_html

app = Flask(__name__)
Bootstrap5(app)


def html_url_to_file_url(year: str, term: str, course: str) -> Path | None:
    if not (part := part_to_year_number(year)):
        return None
    if not (term_name := term_name_to_number(term)):
        return None
    return BASE_FOLDER / part / term_name / course


@app.route("/notes/<year>/<term>/<course>/<pdf_file>.pdf")
def notes_pdf(year: str, term: str, course: str, pdf_file: str):
    if not (folder := html_url_to_file_url(year, term, course)):
        return abort(404)
    file = folder / f"{pdf_file}.pdf"
    if not file.exists():
        return abort(404)
    return send_file(file)


@app.route("/notes/<year>/<term>/<course>/<path:html_file>")
def notes_html(year: str, term: str, course: str, html_file: str):
    if html_file == f"{course}.html":
        html_file = f"{course}_final.html"
    if not (folder := html_url_to_file_url(year, term, course)):
        return abort(404)
    file = folder / f"HTML/{html_file}"
    if not file.exists():
        return abort(404)
    return send_file(file)


@app.route("/notes/<year>/<term>/<course>/HTML/<path:html_file>")
def notes_html_paginated(year: str, term: str, course: str, html_file: str):
    if not (folder := html_url_to_file_url(year, term, course)):
        return abort(404)
    file = folder / f"HTML_paginated/{html_file}"
    if not file.exists():
        return abort(404)
    if html_file.endswith("css"):
        replacements = [
            (r"body {([^}]*)}", ""),
            (r"@media \(prefers-color-scheme: dark\) {[^}]*}", ""),
        ]
        css = f"#pagecontent {{ {file.read_text()} }}"
        for pattern, replacement in replacements:
            css = re.sub(pattern, replacement, css)
        return Response(css, mimetype="text/css")
    if not html_file.endswith("html"):
        return send_file(file)
    content = file.read_text()
    return fix_paginated_html(course, content)


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
    return send_file(BASE_FOLDER / f"{course_code}.apkg")


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


@app.errorhandler(404)
def error_404(error):
    return render_template("404.html")


@app.errorhandler(500)
def erorr_500(error):
    return render_template("500.html")


if __name__ == "__main__":
    load_dotenv()
    debug = os.environ.get("FLASK_DEBUG") is not None
    app.run(port=5005, debug=debug)
