from __future__ import annotations

import datetime
import functools
import os
from pathlib import Path
import re


EXCLUDED_EXTENSIONS = (
    ".apkg",
    ".asy",
    ".aux",
    ".auxlock",
    ".fdb_latexmk",
    ".flashcard",
    ".flashcardout",
    ".fls",
    ".lock",
    ".log",
    ".maf",
    ".mtc",
    ".mtc0",
    ".nix",
    ".out",
    ".pdf",
    ".pre",
    ".ptc1",
    ".ptc2",
    ".ptc3",
    ".ptc4",
    ".ptc5",
    ".ptc6",
    ".ptc7",
    ".ptc8",
    ".ptc9",
    ".gz",
    ".toc",
    ".tsqx",
)


EXTENSION_TO_ICON = {
    ".tex": "braces",
    ".4ht": "braces",
    ".png": "image",
    ".html": "filetype-html",
    ".svg": "filetype-svg",
    ".css": "filetype-css",
    ".html_processed": "file-earmark-binary",
    ".txt": "filetype-txt",
}


@functools.total_ordering
class Item:
    def __init__(self, path: Path) -> None:
        self.path = path

    def is_dir(self) -> bool:
        return self.path.is_dir()

    def __lt__(self, other: Item) -> bool:
        if self.is_dir() and not other.is_dir():
            return True
        if not self.is_dir() and other.is_dir():
            return False
        if self.is_dir() and other.is_dir():
            return self.path.name < other.path.name
        if self.file_extension() == ".tex":
            if other.file_extension() == ".tex":
                if self.path.name.startswith("lecture") and other.path.name.startswith("lecture"):
                    num_self = re.match(r"lecture(\d\d?).tex", self.path.name).group(1)
                    num_other = re.match(r"lecture(\d\d?).tex", other.path.name).group(1)
                    return int(num_self) < int(num_other)
                if self.path.name.startswith("lecture"):
                    return False
                if other.path.name.startswith("lecture"):
                    return True
                return self.path.name < other.path.name
            else:
                return True
        if other.file_extension() == ".tex":
            return False
        return self.path.name < other.path.name

    def __str__(self) -> str:
        if self.is_dir():
            return str(self.path.name) + "/"
        return str(self.path.name)

    def file_extension(self) -> str:
        _, file_extension = os.path.splitext(self.path)
        return file_extension

    def should_exclude(self) -> bool:
        if self.file_extension() in EXCLUDED_EXTENSIONS:
            return True
        return False

    def url(self) -> str:
        if self.is_dir():
            return self.path.name + "/"
        return self.path.name

    def icon_name(self) -> str:
        if self.is_dir():
            return "folder-fill"
        else:
            return EXTENSION_TO_ICON.get(self.file_extension(), "file-earmark")

    def last_edited(self) -> str:
        edited_unix_timestamp = os.path.getmtime(self.path)
        edited_datetime = datetime.datetime.fromtimestamp(edited_unix_timestamp)
        return f"Edited: {edited_datetime.strftime('%a %d %b %Y')}"
