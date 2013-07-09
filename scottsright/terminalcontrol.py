"""
Terminal control sequences

see: https://en.wikipedia.org/wiki/ANSI_escape_code#CSI_codes

inspired by
https://github.com/gwk/gloss/blob/master/python/gloss/io/cs.py
"""

import re
import logging

QUERY_CURSOR_POSITION = "\x1b[6n"
SCROLL_DOWN = "D"
CURSOR_UP, CURSOR_DOWN, CURSOR_FORWARD, CURSOR_BACK = ["[%s" for char in 'ABCD']
ERASE_REST_OF_LINE = "[K"
ERASE_LINE = "[2K"

def produce_simple_sequence(char):
    def func(self):
        self.out_stream.write(char)
    return func

def produce_cursor_sequence(char):
    """Returns a method that issues a cursor control sequence."""
    def func(self, n=1):
        if n: self.out_stream.write("[%d%s" % (n, char))
    return func

class TCPartialler(object):
    """Returns terminal control functions partialed for stream returned by
    stream_getter on att lookup"""
    def __init__(self, in_stream_getter, out_stream_getter, in_buffer_getter):
        self.in_stream_getter = in_stream_getter
        self.out_stream_getter = out_stream_getter
        self.in_buffer_getter = in_buffer_getter

    in_stream = property(lambda self: self.in_stream_getter())
    out_stream = property(lambda self: self.out_stream_getter())
    in_buffer = property(lambda self: self.in_buffer_getter())

    up, down, forward, back = [produce_cursor_sequence(c) for c in 'ABCD']
    fwd = forward
    query_cursor_position = produce_simple_sequence(QUERY_CURSOR_POSITION)
    scroll_down = produce_simple_sequence(SCROLL_DOWN)
    erase_rest_of_line = produce_simple_sequence(ERASE_REST_OF_LINE)
    erase_line = produce_simple_sequence(ERASE_LINE)

    def retrying_read(self):
        while True:
            try:
                return self.in_stream.read(1)
            except IOError:
                logging.debug('read interrupted, retrying')

    def get_screen_position(self):
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

    def set_screen_position(self, (row, col)):
        self.out_stream.write("[%d;%dH" % (row, col))

    def get_screen_size(self):
        #TODO generalize get_screen_position code and use it here instead
        orig = self.get_screen_position()
        self.fwd(10000) # 10000 is much larger than any reasonable terminal
        self.down(10000)
        size = self.get_screen_position()
        self.set_screen_position(orig)
        return size

if __name__ == '__main__':
    for k in globals().keys():
        print k

    import cStringIO
    fake = cStringIO.StringIO()
    t = TCPartialler(lambda: fake)
    t.scroll_down()
    fake.seek(0)
    print repr(fake.read())

