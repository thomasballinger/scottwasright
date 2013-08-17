"""
Terminal control sequences

see: https://en.wikipedia.org/wiki/ANSI_escape_code#CSI_codes

inspired by
https://github.com/gwk/gloss/blob/master/python/gloss/io/cs.py
"""

import os
import sys
import tty
import signal
import re
import subprocess
import logging

import events


_SIGWINCH_COUNTER = 0

QUERY_CURSOR_POSITION = "\x1b[6n"
SCROLL_DOWN = "D"
CURSOR_UP, CURSOR_DOWN, CURSOR_FORWARD, CURSOR_BACK = ["[%s" for char in 'ABCD']
ERASE_REST_OF_LINE = "[K"
ERASE_LINE = "[2K"


def produce_simple_sequence(seq):
    def func(out_stream):
        out_stream.write(seq)
    return func

def produce_cursor_sequence(char):
    """Returns a method that issues a cursor control sequence."""
    def func(self, n=1):
        if n: self.out_stream.write("[%d%s" % (n, char))
    return func

class TerminalController(object):
    """Returns terminal control functions partialed for stream returned by
    stream_getter on att lookup"""
    def __init__(self, in_stream=sys.stdin, out_stream=sys.stdout):
        self.in_stream = in_stream
        self.out_stream = out_stream
        self.in_buffer = []
        self.sigwinch_counter = _SIGWINCH_COUNTER - 1

    def __enter__(self):
        def signal_handler(signum, frame):
            global _SIGWINCH_COUNTER
            _SIGWINCH_COUNTER += 1
        signal.signal(signal.SIGWINCH, signal_handler)

        #TODO implement this with termios/tty instead of subprocess
        self.original_stty = subprocess.check_output(['stty', '-g'])
        tty.setraw(self.in_stream)
        return self

    def __exit__(self, type, value, traceback):
        signal.signal(signal.SIGWINCH, lambda: None)
        os.system('stty '+self.original_stty)

    up, down, forward, back = [produce_cursor_sequence(c) for c in 'ABCD']
    fwd = forward
    query_cursor_position = produce_simple_sequence(QUERY_CURSOR_POSITION)
    scroll_down = produce_simple_sequence(SCROLL_DOWN)
    erase_rest_of_line = produce_simple_sequence(ERASE_REST_OF_LINE)
    erase_line = produce_simple_sequence(ERASE_LINE)

    def get_event(self):
        """Blocks and returns the next event"""
        #TODO make this cooler - generator? Trie?
        chars = []
        while True:
            #logging.debug('checking if instance counter (%d) is less than global (%d) ' % (self.sigwinch_counter, _SIGWINCH_COUNTER))
            if self.sigwinch_counter < _SIGWINCH_COUNTER:
                self.sigwinch_counter = _SIGWINCH_COUNTER
                self.in_buffer = chars + self.in_buffer
                return events.WindowChangeEvent(*self.get_screen_size())
            if chars == ['\x1b', '\x1b']:
                return '\x1b'
            if chars and chars[0] != '\x1b':
                return ''.join(chars)
            if len(chars) == 2 and chars[1] != '[':
                return ''.join(chars)
            if len(chars) > 2 and chars[1] == '[' and chars[-1] not in tuple('1234567890;'):
                return ''.join(chars)
            if self.in_buffer:
                chars.append(self.in_buffer.pop(0))
                continue
            try:
                chars.append(self.in_stream.read(1))
            except IOError:
                continue

    def retrying_read(self):
        while True:
            try:
                return self.in_stream.read(1)
            except IOError:
                logging.debug('read interrupted, retrying')

    def write(self, msg):
        self.out_stream.write(msg)

    def get_cursor_position(self):
        """Returns the terminal (row, column) of the cursor"""
        self.query_cursor_position()
        resp = ''
        while True:
            c = self.retrying_read()
            resp += c
            m = re.search('(?P<extra>.*)\x1b\[(?P<row>\\d+);(?P<column>\\d+)R', resp)
            if m:
                row = int(m.groupdict()['row'])
                col = int(m.groupdict()['column'])
                self.in_buffer.extend(list(m.groupdict()['extra']))
                return (row, col)

    def set_cursor_position(self, (row, col)):
        self.out_stream.write("[%d;%dH" % (row, col))

    def get_screen_size(self):
        #TODO generalize get_cursor_position code and use it here instead
        orig = self.get_cursor_position()
        self.fwd(10000) # 10000 is much larger than any reasonable terminal
        self.down(10000)
        size = self.get_cursor_position()
        self.set_cursor_position(orig)
        return size

def test():
    with TerminalController() as tc:
        pos = str(tc.get_cursor_position())
        tc.write(pos)
        tc.back(len(pos))
        tc.scroll_down()
        tc.write('asdf')
        tc.back(4)
        tc.scroll_down()
        tc.write('asdf')
        tc.back(4)
        while True:
            e = tc.get_event()
            tc.write(repr(e))
            tc.scroll_down()
            tc.back(len(repr(e)))
            if e == '':
                sys.exit()

if __name__ == '__main__':
    test()

