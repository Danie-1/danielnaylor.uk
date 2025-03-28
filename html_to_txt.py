import re
from html.parser import HTMLParser
from io import StringIO
from pathlib import Path


class MLStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()

    def handle_data(self, data: str) -> None:
        self.text.write(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("li", "ul"):
            self.text.write("\n\n")

    def handle_endtag(self, tag: str) -> None:
        if not tag.startswith("mjx"):
            self.text.write("\n")
        if tag in ("li", "ul"):
            self.text.write("\n\n")

    def get_data(self) -> str:
        return self.text.getvalue()


def strip_tags(html: str) -> str:
    s = MLStripper()
    s.feed(html)
    return s.get_data()


def process_math(match: re.Match[str]) -> str:
    inline = 'display="inline"' in match.group(0)
    output = match.group(0)
    output = output.replace("\u2061", " ")
    output = strip_tags(output).strip()
    output = output.replace("\n", " ")
    output = re.sub(r"\s+", " ", output)
    if inline:
        return f"STARTMATH{output}ENDMATH"
    else:
        return f"\n\n\\[\n{output}\n\\]\n\n"


def process_paragraph(match: re.Match[str]) -> str:
    text = match.group(0)
    if text.startswith("\\["):
        return text
    text = re.sub(r"\n([,.?:])", r"\1", text)
    text = text.replace("\n", " ")
    return text


def concat_paragraph_lines(text: str) -> str:
    while (
        new_text := re.sub(
            r"(?<=\n\n).*?(?=\n\n)", process_paragraph, text, flags=re.DOTALL
        )
    ) != text:
        text = new_text
    return text


def wrap_line(line: str) -> str:
    output_lines = []
    current_line = ""
    for word in line.split(" "):
        if len(f"{current_line} {word}") > 80:
            output_lines.append(current_line)
            current_line = ""
        if current_line:
            current_line = f"{current_line} {word}"
        else:
            current_line = word
    output_lines.append(current_line)
    return "\n".join(output_lines)


def wrap_lines(text: str) -> str:
    return "\n".join([wrap_line(line) for line in text.splitlines()])


def html2text(html: str) -> str:
    output = html
    output = re.sub(r"<title>.*?</title>", "", output)
    output = re.sub(r"<style[^>]*>.*?</style>", "", output, flags=re.DOTALL)
    output = re.sub(r"<script[^>]*>.*?</script>", "", output, flags=re.DOTALL)
    output = re.sub(r"<math[^>]*>.*?</math>", process_math, output, flags=re.DOTALL)
    output = strip_tags(output).strip()
    output = re.sub(r"\[(?:next|next-tail|prev|prev-tail|up|tail|front)\s*\]", "", output).strip()
    output = re.sub(r"STARTMATH", "", output)
    output = re.sub(r"ENDMATH", "", output)
    output = re.sub(r" +", " ", output)
    output = re.sub(r"\n *", "\n", output)
    output = re.sub(r"(\n\s*)+\n", "\n\n", output)
    output = re.sub(
        r"^(\((?:[ivx]{1,4}|[abcdefghijklmnopqrstuvwxyz])\)) *\n\n",
        r"\1 ",
        output,
        flags=re.MULTILINE,
    )
    output = re.sub(
        r"""(?x)
        (
            (?:
                Theorem
                |Lemma
                |Proposition
                |Corollary
                |Definition
                |Example
                |Notation
                |Conjecture
            )\s*
            (?:
                \d+
                (?:\.\d+){0,2}
            )?
            (?:
                \(
                    .*?
                \)
            )?
            \.
        )\n
        """,
        r"\1",
        output,
    )
    output = re.sub(r"(Proof.?\.)\n", r"\1", output)
    output = concat_paragraph_lines(output)
    output = wrap_lines(output)
    return output
