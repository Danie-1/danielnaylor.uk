import asyncio
import re
from contextlib import asynccontextmanager
from typing import AsyncIterator

from asonic import Client
from asonic.client import Channel
from flask import url_for

from generate_webpage import get_course_from_course_code
from html_to_txt import html2text
from haystack_highlighter import Highlighter


@asynccontextmanager
async def create_search_client() -> AsyncIterator[Client]:
    client = Client(host="search")
    await client.channel(Channel.SEARCH)
    yield client
    await client.quit()


class SearchResult:
    def __init__(self, query: str, file_path: str) -> None:
        year, term, course_code, html, file_name = file_path.split("/")
        course = get_course_from_course_code(course_code)
        assert course
        file = course.path / "HTML_paginated" / file_name
        file_text = file.read_text()
        self.text = html2text(file_text)
        self.highlighted = Highlighter(query).highlight(self.text.replace("\n", " "))
        self.title = (
            re.search(r"<title>(.*?)</title>", file_text)
            .group(1)
            .rsplit("-", maxsplit=1)[0]
            .strip()
        )
        self.href = url_for(
            "notes_html",
            year=year,
            term=term,
            course=course_code,
            html_file=f"HTML/{file_name}",
        )


async def search_htmls(query: str) -> list[SearchResult]:
    async with create_search_client() as search_client:
        return [
            SearchResult(query, result.decode())
            for result in await search_client.query("html_notes", "default", query)
        ]


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    print(loop.run_until_complete(search_htmls("isomorphism")))
