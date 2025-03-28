from contextlib import asynccontextmanager
import re
from typing import AsyncIterator

from asonic import Client
from asonic.client import Channel
from asonic.connection import asyncio

from generate_webpage import Course, get_courses
from html_to_txt import html2text


@asynccontextmanager
async def create_ingest_client() -> AsyncIterator[Client]:
    client = Client(host="search")
    await client.channel(Channel.INGEST)
    yield client
    await client.quit()


async def index_course(course: Course) -> None:
    path = course.path / "HTML_paginated"
    if not path.exists():
        return
    async with create_ingest_client() as ingest_client:
        for html_file in path.glob("*.html"):
            text = html2text(html_file.read_text())
            text = re.sub(r"[^a-z0-9A-Z]", " ", text)
            # html_file.with_suffix(".txt").write_text(text)
            key = str(
                course.part.part_name
                + "/"
                + course.term.term_name
                + "/"
                + course.course_code
                + "/HTML/"
                + html_file.name
            )
            text = text.replace("\n", " ")
            await ingest_client.flusho("html_notes", "default", key)
            await ingest_client.push("html_notes", "default", key, text)


async def index_all_htmls() -> None:
    for course in get_courses():
        await index_course(course)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(index_all_htmls())
    print("Finished indexing HTML files")
