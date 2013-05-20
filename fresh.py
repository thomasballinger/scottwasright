"""
Terminal wrapper that can be written to by a numpy array

"""

import numpy
import signal
import tty
import sys
import re
import functools
import os
from itertools import izip

class Terminal(object):

    def __init__(self, in_stream, out_stream):
        tty.setraw(in_stream)
        self.in_buffer = []
        self.in_stream = in_stream
        self.out_stream = out_stream
        signal.signal(signal.SIGWINCH, lambda signum, frame: self.window_change_event())

    def render_to_terminal(self, array, cursor_position=(0,0)):
        """the thing that's hard to test

        If array received is of width too small, render it anyway
        if array received is of width too large, render it anyway
        if array received is of height too small, render it anyway
        if array received is of height too large, render it, scroll down,
            and render the rest of it, then return how much we scrolled down
        """
        #TODO add cool render-on-change caching

        # BUG! Both izip and zip consume an additional element off of rows
        # if lines ends first!
        height, width = self.get_screen_size()
        lines = iter(array)
        rows = iter(range(1, height+1))
        for row, line in izip(rows, lines):
            self.set_screen_pos((row, 1))
            self.out_stream.write(''.join(line[:(width+1)]))
        for row in rows: # if array too small
            self.set_screen_pos((row, 1))
            self.erase_line()
        scrolls = 0
        for line in lines: # if array too big
            scrolls += 1
            self.out_stream.write("D")
            self.set_screen_pos((height, 1)) # since scrolling moves the cursor
            self.out_stream.write("".join(line[:(width+1)]))
        self.set_screen_pos((cursor_position[0] - scrolls + 1, cursor_position[1] + 1))
        return scrolls

    def window_change_event(self):
        raise Exception("Window Change Event")
        #TODO this should be in the same input stream, so we need concurrency?

    def get_char(self):
        if self.in_buffer:
            return self.in_buffer.pop(0)
        else:
            return self.in_stream.read(1)

    def _move_cursor_direction(char):
        def func(self, n=1):
            if n: self.out_stream.write("[%d%s" % (n, char))
        return func
    up, down, fwd, back = [_move_cursor_direction(char) for char in 'ABCD']

    def erase_rest_of_line(self): self.out_stream.write("[K")
    def erase_line(self): self.out_steam.write("[2K")
    QUERY_CURSOR_POSITION = "\x1b[6n"

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
        #TODO generalize get_screen_position code and use it here instead
        orig = self.get_screen_position()
        self.fwd(10000)
        self.down(10000)
        size = self.get_screen_position()
        self.set_screen_pos(orig)
        return size

    def array_from_text(self, msg):
        rows, columns = self.get_screen_size()
        a = numpy.array([[' ' for _ in range(columns)] for _ in range(rows)])
        i = 0
        for c in msg:
            if i >= a.size:
                return a
            elif c in '\r\n':
                i = ((i / columns) + 1) * columns
            else:
                a.flat[i] = c
            i += 1
        return a

def test():
    t = Terminal(sys.stdin, sys.stdout)
    rows, columns = t.get_screen_size()
    while True:
        c = t.get_char()
        if c == "":
            sys.exit()
        elif c == "h":
            t.render_to_terminal(t.array_from_text("a for small array"))
        elif c == "a":
            t.render_to_terminal(numpy.array([[c] * columns for _ in range(rows)]))
        elif c == "s":
            t.render_to_terminal(numpy.array([[c] * columns for _ in range(rows-1)]))
        elif c == "d":
            t.render_to_terminal(numpy.array([[c] * columns for _ in range(rows+1)]))
        elif c == "":
            [t.out_stream.write('\n') for _ in range(rows)]
        else:
            t.render_to_terminal(t.array_from_text("unknown command"))

def main():
    t = Terminal(sys.stdin, sys.stdout)
    rows, columns = t.get_screen_size()
    import random
    goop = lambda l: [random.choice('aaabcddeeeefghiiijklmnooprssttuv        ') for _ in range(l)]
    a = numpy.array([goop(columns) for _ in range(rows)])
    #for char in inputStream():
    t.render_to_terminal(a)
    while True:
        c = t.get_char()
        if c == "":
            sys.exit()
        t.render_to_terminal(numpy.array([[c] * columns for _ in range(rows)]))

def safe_run(f):
    try:
        f()
    finally:
        os.system('reset')

def test_array_from_text():
    t = Terminal(sys.stdin, sys.stdout)
    a = t.array_from_text('\n\nhey there\nyo')
    os.system('reset')
    for line in a:
        print ''.join(line)
    raw_input()

if __name__ == '__main__':
    #safe_run(test_array_from_text)
    safe_run(test)

