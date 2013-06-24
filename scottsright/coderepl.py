import sys
import logging
import code
import scottsright.repl

logging.basicConfig(level=logging.DEBUG, filename='coderepl.log')

class CodeRepl(scottsright.repl.Repl):
    def __init__(self):
        super(CodeRepl, self).__init__()
        self.interp = code.InteractiveInterpreter()
        self.buffer = []

    def push(self, line):
        """Run a line of code.

        Return ("for stdout", "for_stderr", finished?)
        """
        self.buffer.append(line)
        out_spot = sys.stdout.tell()
        err_spot = sys.stderr.tell()
        unfinished = self.interp.runsource('\n'.join(self.buffer))
        sys.stdout.seek(out_spot)
        sys.stderr.seek(err_spot)
        out = sys.stdout.read()
        err = sys.stderr.read()
        if unfinished and not err:
            logging.debug('unfinished - line added to buffer')
            return (None, None, False)
        else:
            logging.debug('finished - buffer cleared')
            self.buffer = []
            return (out[:-1], err[:-1], True)

def test():
    with CodeRepl() as r:
        r.display_line_width = 50
        while True:
            scrolled = r.dumb_print_output(20, 50)
            r.scroll_offset += scrolled
            r.dumb_input()

if __name__ == '__main__':
    test()
