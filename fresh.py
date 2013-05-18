

import numpy
import signal
import tty
import sys
import re
import functools

def move_cursor_direction(char, n=1):
    if n: sys.stdout.write("[%d%s" % (n, char))
up, down, fwd, back = [functools.partial(move_cursor_direction, char) for char in 'ABCD']

def erase_rest_of_line(): sys.stdout.write("[K")
def erase_line(): sys.stdout.write("[2K")


class Terminal(object):
    """I

    in_stream should be in raw mod"""

    QUERY_CURSOR_POSITION = "\x1b[6n"

    def __init__(self, in_stream, out_stream):
        tty.setraw(in_stream)
        self.in_buffer = []
        self.in_stream = in_stream
        self.out_stream = out_stream
        signal.signal(signal.SIGWINCH, lambda signum, frame: self.window_change_event())

    def render_to_terminal(self, array):
        """the thing that's hard to test

        assumes we're in raw mode
        """
        for i, line in zip(range(1, array.shape[0]+1), array):
            self.set_screen_pos((i, 1))
            self.out_stream.write(''.join(line))

    def window_change_event(self):
        raise Exception("Window Change Event")

    def get_char(self):
        if self.in_buffer:
            return self.in_buffer.pop(0)
        else:
            self.in_stream.read(1)

    def get_screen_position(self):
        """Returns the terminal (row, column) of the cursor"""
        sys.stdout.write(Terminal.QUERY_CURSOR_POSITION)
        resp = ''
        while True:
            c = self.in_stream.read(1)
            resp += c
            m = re.search('(?P<extra>.*)\x1b\[(?P<row>\\d+);(?P<column>\\d+)R', resp)
            if m:
                row = int(m.groupdict()['row'])
                col = int(m.groupdict()['column'])
                self.in_buffer.extend(list(m.groupdict()['extra']))
                return (row, col)

    def set_screen_pos(self, (row, col)):
        sys.stdout.write("[%d;%dH" % (row, col))

    def get_screen_size(self):
        orig = self.get_screen_position()
        fwd(10000)
        down(10000)
        size = self.get_screen_position()
        self.set_screen_pos(orig)
        return size

def main():
    t = Terminal(sys.stdin, sys.stdout)
    rows, columns = t.get_screen_size()
    import random
    a = numpy.array([[random.choice('abcde')]*columns for _ in range(rows)])
    #for char in inputStream():
    t.render_to_terminal(a)

if __name__ == '__main__':
    main()
