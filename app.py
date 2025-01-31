import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, abort, redirect, render_template, send_file
from flask_bootstrap import Bootstrap5

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


@app.route("/notes/<year>/<term>/<course>/<html_file>")
def notes_html(year: str, term: str, course: str, html_file: str):
    if html_file == f"{course}.html":
        html_file = f"{course}_final.html"
    return send_file(html_url_to_file_url(year, term, course) / f"HTML/{html_file}")


@app.route("/notes/<year>/<term>/<course>/images/<image_name>")
def notes_html_images(year: str, term: str, course: str, image_name: str):
    return send_file(html_url_to_file_url(year, term, course) / f"HTML/images/{image_name}")


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


@app.route("/notes_old/")
def notes_home():
    term_list = [term for year in get_years() for term in year.get_terms()]
    return render_template("notes_old.html", terms=term_list)


@app.route("/notes/")
def notes_test():
    term_list = [term for year in get_years() for term in year.get_terms()]
    return render_template("notes.html", terms=term_list)


@app.route("/")
def home():
    return send_file("./templates/home.html")


if __name__ == "__main__":
    load_dotenv()
    debug = os.environ.get("FLASK_DEBUG") is not None
    app.run(port=5005, debug=debug)
