import re
from itertools import chain
from typing import Iterator

from markupsafe import Markup


class Highlighter:
    def __init__(
        self,
        query: str,
        css_class: str = "fw-bold",
        html_tag: str = "span",
        max_length: int = 500,
    ) -> None:
        self.css_class = css_class
        self.html_tag = html_tag
        self.max_length = max_length
        self.query_words = {
            word.lower() for word in query.split() if not word.startswith("-")
        }

    def highlight(self, text: str) -> str:
        chunks_to_use = []
        total_length = 0
        for chunk in self.get_chunk_texts(text):
            if total_length + len(chunk) > self.max_length:
                break
            chunks_to_use.append(chunk)
            total_length += len(chunk)
        output = " ... ".join(chunk.strip() for chunk in chunks_to_use)
        for word in self.query_words:
            output = re.sub(
                rf"(?i)({word})",
                rf'<{self.html_tag} class="{self.css_class}">\1</{self.html_tag}>',
                output,
            )
        return Markup(output)

    def find_word_locations(self, text: str) -> dict[str, list[int]]:
        word_locations: dict[str, list[int]] = {}
        lower_text_block = text.lower()
        for word in self.query_words:
            if word not in word_locations:
                word_locations[word] = []
            start_offset = 0
            while start_offset < len(text):
                next_offset = lower_text_block.find(word, start_offset)
                if next_offset == -1:
                    break
                word_locations[word].append(next_offset)
                start_offset = next_offset + len(word)
        return word_locations

    def get_unclipped_chunks(self, text: str) -> list[tuple[int, int]]:
        word_locations = sorted(chain(*self.find_word_locations(text).values()))
        chunks: list[tuple[int, int]] = []
        if not word_locations:
            return []
        current_chunk_start = max(0, word_locations[0] - 30)
        current_chunk_end = min(len(text), word_locations[0] + 35)
        for position in word_locations:
            if position < current_chunk_end:
                current_chunk_end = min(len(text), position + 35)
                continue
            chunks.append((current_chunk_start, current_chunk_end))
            current_chunk_start = max(0, position - 30)
            current_chunk_end = min(len(text), position + 35)
        chunks.append((current_chunk_start, current_chunk_end))
        return chunks

    def get_chunks(self, text: str) -> list[tuple[int, int]]:
        output = []
        for start, end in self.get_unclipped_chunks(text):
            if start != 0 and text[start - 1] != " ":
                start = text.find(" ", start, end) + 1
            if end != len(text) and text[end] != " ":
                end = text.rfind(" ", start, end)
            output.append((start, end))
        return output

    def get_chunk_texts(self, text: str) -> Iterator[str]:
        for start, end in self.get_chunks(text):
            yield text[start:end]
