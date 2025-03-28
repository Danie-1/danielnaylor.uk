import os
import pickle
import re
from pathlib import Path

from dotenv import load_dotenv
from flask import (
    Flask,
    Response,
    abort,
    g,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired

from generate_webpage import (
    BASE_FOLDER,
    get_course_from_alias,
    get_course_from_course_code,
    get_years,
    part_to_year_number,
    term_name_to_number,
)
from html_fixing import fix_paginated_html
from search import search_htmls
from source_items import Item

app = Flask(__name__)
Bootstrap5(app)


class SearchForm(FlaskForm):
    q = StringField("Search", validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if "formdata" not in kwargs:
            kwargs["formdata"] = request.args
        if "meta" not in kwargs:
            kwargs["meta"] = {"csrf": False}
        super(SearchForm, self).__init__(*args, **kwargs)


@app.before_request
def before_request():
    g.search_form = SearchForm()


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


@app.route("/notes/<year>/<term>/<course_code>/sources/", defaults={"file_path": ""})
@app.route("/notes/<year>/<term>/<course_code>/sources/<path:file_path>")
def notes_sources(year: str, term: str, course_code: str, file_path: str):
    if not (folder := html_url_to_file_url(year, term, course_code)):
        return abort(404)
    if not (course := get_course_from_course_code(course_code)):
        return abort(404)
    file = folder / file_path
    if file.is_dir():
        if not file_path.endswith("/") and not file_path == "":
            return redirect(
                url_for(
                    "notes_sources",
                    year=year,
                    term=term,
                    course_code=course_code,
                    file_path=file_path + "/",
                )
            )
        term_folder = folder.parent
        relative_path = os.path.relpath(file, term_folder)
        base_url = url_for(
            "notes_sources", year=year, term=term, course_code=course_code
        )
        url_extra = ""
        breadcrumbs = [
            (
                p,
                base_url
                + (url_extra := url_extra + (f"{p}/" if p != course_code else "")),
            )
            for p in relative_path.split("/")
        ]
        return render_template(
            "sources_dir.html",
            course_name=course.course_name,
            folder_name=f"{course_code}/{file_path}",
            items=sorted(Item(i) for i in file.glob("*")),
            breadcrumbs=breadcrumbs,
        )
    if file_path.endswith("/"):
        return redirect(
            url_for(
                "notes_sources",
                year=year,
                term=term,
                course_code=course_code,
                file_path=file_path.rstrip("/"),
            )
        )
    base, ext = os.path.splitext(file.name)
    if ext in (".tex", ".html", ".css", ".txt", ".4ht") or base in (
        ".ignore",
        "htmlyes",
    ):
        return send_file(file, mimetype="text/plain")
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
    file_processed = folder / f"HTML_paginated/{html_file}_processed"
    if file_processed.exists():
        with open(file_processed, "rb") as f:
            data = pickle.load(f)
            return render_template("notes_paginated.html", course_code=course, **data)
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


@app.route("/notes/search")
async def notes_search():
    if not g.search_form.validate():
        return abort(500)
    query = g.search_form.q.data
    return render_template("notes_search.html", query=query, results=await search_htmls(query))


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
    return render_template("404.html"), 404


@app.errorhandler(500)
def erorr_500(error):
    return render_template("500.html"), 500


if __name__ == "__main__":
    load_dotenv()
    debug = os.environ.get("FLASK_DEBUG") is not None
    app.run(port=5005, debug=debug)
