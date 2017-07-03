# type reference in comments confuses pylint
#pylint: disable=W0611
from typing import List


class CodeWriter:
    def __init__(self) -> None:
        self.lines = []  # type: List[str]
        self.indent = 0

    def line(self, text: str) -> None:
        self.lines.append((" " * self.indent) + text)

    def blank_line(self) -> None:
        self.lines.append("")

    def increase_indent(self) -> None:
        self.indent += 4

    def decrease_indent(self) -> None:
        if self.indent <= 0:
            raise Exception('indent cannot be negative')
        self.indent -= 4

    def result(self) -> str:
        return "\n".join(self.lines)
