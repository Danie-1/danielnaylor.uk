from pathlib import Path

from flask import Flask, abort, redirect, send_file

from generate_webpage import (
    BASE_FOLDER,
    generate_homepage,
    get_course_from_alias,
    get_course_from_course_code,
    part_to_year_number,
    term_name_to_number,
)


app = Flask(__name__)


def html_url_to_file_url(year: str, term: str, course: str) -> Path:
    return BASE_FOLDER / part_to_year_number(year) / term_name_to_number(term) / course


@app.route("/notes/<year>/<term>/<course>/<pdf_file>.pdf")
def notes_pdf(year: str, term: str, course: str, pdf_file: str):
    return send_file(html_url_to_file_url(year, term, course) / f"{pdf_file}.pdf")


@app.route("/notes/<year>/<term>/<course>/<html_file>")
def notes_html(year: str, term: str, course: str, html_file: str):
    if html_file == f"{course}.html":
        html_file = f"{course}_final.html"
    return send_file(html_url_to_file_url(year, term, course) / f"HTML/{html_file}")


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
    if not (course := get_course_from_course_code(course_code)):
        return abort(404)
    return send_file(BASE_FOLDER / f"{course_code.upper()}.apkg")


@app.route("/")
def home():
    return generate_homepage()


if __name__ == "__main__":
    app.run(port=5004)
