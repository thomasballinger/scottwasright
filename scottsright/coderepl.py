import sys
import logging
import re
import code

from bpython.autocomplete import Autocomplete

import scottsright.repl

logging.basicConfig(level=logging.DEBUG, filename='coderepl.log')

INDENT_AMOUNT = 4

class CodeRepl(scottsright.repl.Repl):
    def __init__(self):
        super(CodeRepl, self).__init__()
        self.interp = code.InteractiveInterpreter()
        self.buffer = []
        self.completer = Autocomplete(self.interp.locals)

    def __repr__(self):
        cw = self.current_word
        if cw:
            self.completer.complete(cw, 0)
            return str(cw) + '\n' + str(self.completer.matches)[:70]
        else:
            return 'no current word:\n' + repr(re.split(r'([\w_][\w0-9._]+)', self.current_line))

    def push(self, line):
        """Run a line of code.

        Return ("for stdout", "for_stderr", finished?)
        """
        self.buffer.append(line)
        indent = len(re.match(r'[ ]*', line).group())
        self.indent_levels = [l for l in self.indent_levels if l < indent] + [indent]

        if line.endswith(':'):
            self.indent_levels.append(indent + INDENT_AMOUNT)
        elif line and line.count(' ') == len(self.current_line) == self.indent_levels[-1]:
            self.indent_levels.pop()
        out_spot = sys.stdout.tell()
        err_spot = sys.stderr.tell()
        unfinished = self.interp.runsource('\n'.join(self.buffer))
        sys.stdout.seek(out_spot)
        sys.stderr.seek(err_spot)
        out = sys.stdout.read()
        err = sys.stderr.read()
        if unfinished and not err:
            logging.debug('unfinished - line added to buffer')
            return (None, None, False, self.indent_levels[-1])
        else:
            logging.debug('finished - buffer cleared')
            self.buffer = []
            if err:
                self.indent_levels = [0]
            return (out[:-1], err[:-1], True, self.indent_levels[-1])

def test():
    with CodeRepl() as r:
        r.display_line_width = 50
        while True:
            scrolled = r.dumb_print_output(20, 50)
            r.scroll_offset += scrolled
            r.dumb_input()

if __name__ == '__main__':
    test()
