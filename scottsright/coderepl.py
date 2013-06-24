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
        logging.debug('line to be run: %s', line)
        self.buffer.append(line)
        out_spot = sys.stdout.tell()
        err_spot = sys.stderr.tell()
        logging.debug('err_spot : %s', err_spot)
        logging.debug('out_spot : %s', out_spot)
        unfinished = self.interp.runsource('\n'.join(self.buffer))
        logging.debug('locals after run: %s', self.interp.locals.keys())
        logging.debug('return value : %s', unfinished)
        sys.stdout.seek(out_spot)
        sys.stderr.seek(err_spot)
        out = sys.stdout.read()
        err = sys.stderr.read()
        logging.debug('out : %s', out)
        logging.debug('err : %s', err)
        self.orig_stderr.seek(0)
        if unfinished and not err:
            logging.debug('unfinished - line added to buffer')
            return (None, None, False)
        else:
            logging.debug('finished - buffer cleared')
            self.buffer = []
            return (out, err, True)

def test():
    with CodeRepl() as r:
        r.display_line_width = 50
        while True:
            scrolled = r.dumb_print_output(20, 50)
            r.scroll_offset += scrolled
            r.dumb_input()

if __name__ == '__main__':
    test()
