from __future__ import annotations

import functools
from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader


load_dotenv()

BASE_FOLDER = Path(os.environ["BASE_FOLDER"])


@dataclass
@functools.total_ordering
class Part:
    path: Path

    @property
    def part_name(self) -> str:
        with open(self.path / "title.txt") as f:
            return f.read().strip()

    def get_terms(self) -> list[Term]:
        return sorted(
            (Term(i) for i in self.path.glob("term*")), key=lambda term: term.path.name
        )

    def __le__(self, other: Part) -> bool:
        return self.path.name <= other.path.name


@dataclass
@functools.total_ordering
class Course:
    path: Path

    @property
    def course_name(self) -> str:
        with open(self.path / "title.txt") as f:
            return f.read().strip()

    @property
    def course_code(self) -> str:
        return self.path.name

    @property
    def term(self) -> Term:
        return Term(self.path.parent)

    @property
    def part(self) -> Part:
        return self.term.part

    @property
    def notes_exist(self) -> bool:
        return (self.path / f"{self.path.name}.pdf").exists() or (
            self.path / "lecture1.pdf"
        ).exists()

    @property
    def flashcards_exist(self) -> bool:
        return (BASE_FOLDER / f"{self.path.name}.apkg").exists()

    @property
    def html_exists(self) -> bool:
        return (self.path / "HTML").exists()

    def url(self) -> str:
        return f"/notes/{self.part.part_name}/{self.term.term_name}/{self.course_code}"

    def pdf_url(self) -> str:
        if not (self.path / f"{self.path.name}.pdf").exists():
            return f"{self.url()}/lecture1.pdf"
        return f"{self.url()}/{self.course_code}.pdf"

    def html_url(self) -> str:
        return f"{self.url()}/{self.course_code}.html"

    def __le__(self, other: Course) -> bool:
        return self.path.name <= other.path.name

    def get_acronyms(self) -> list[str]:
        aliases = (self.path / "aliases.txt").read_text().splitlines()
        return list(
            set(alias.lower() for alias in aliases + [self.course_code.lower()])
        )


@dataclass
@functools.total_ordering
class Term:
    path: Path

    @property
    def term_name(self) -> str:
        with open(self.path / "title.txt") as f:
            return f.read().strip()

    @property
    def part(self) -> Part:
        return Part(self.path.parent)

    def __le__(self, other: Term) -> bool:
        return self.path.name <= other.path.name

    def get_courses(self) -> list[Course]:
        return sorted(
            (Course(course) for course in self.path.glob("*") if course.is_dir()),
            key=lambda course: course.path.name,
        )


def get_years() -> list[Part]:
    years = [Part(i) for i in BASE_FOLDER.glob("year*")]
    years.sort()
    return years


def generate_notes_homepage() -> str:
    term_list = [term for year in get_years() for term in year.get_terms()]

    environment = Environment(loader=FileSystemLoader("templates/"))
    template = environment.get_template("notes.html")

    return template.render(terms=term_list)


def part_to_year_number(part: str) -> str:
    return {
        "IA": "year1",
        "IB": "year2",
        "II": "year3",
        "III": "year4",
    }[part]


def term_name_to_number(term_name: str) -> str:
    return {
        "Michaelmas": "term1",
        "Lent": "term2",
        "Easter": "term3",
    }[term_name]


def get_courses() -> list[Course]:
    return [
        course
        for year in get_years()
        for term in year.get_terms()
        for course in term.get_courses()
    ]


def get_course_from_alias(acronym: str) -> Course | None:
    for course in get_courses():
        if acronym.lower() in course.get_acronyms():
            return course
    return None


def get_course_from_course_code(course_code: str) -> Course | None:
    for course in get_courses():
        if course_code.lower() == course.course_code.lower():
            return course
    return None
