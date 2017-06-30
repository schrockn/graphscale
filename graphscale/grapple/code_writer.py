class CodeWriter:
    def __init__(self):
        self.lines = []
        self.indent = 0

    def line(self, text):
        self.lines.append((" " * self.indent) + text)

    def blank_line(self):
        self.lines.append("")

    def increase_indent(self):
        self.indent += 4

    def decrease_indent(self):
        if self.indent <= 0:
            raise Exception('indent cannot be negative')
        self.indent -= 4

    def result(self):
        return "\n".join(self.lines)