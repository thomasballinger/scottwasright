"""
Terminal control sequences

see: https://en.wikipedia.org/wiki/ANSI_escape_code#CSI_codes

inspired by
https://github.com/gwk/gloss/blob/master/python/gloss/io/cs.py
"""

import functools
import inspect
import re

import logging

QUERY_CURSOR_POSITION = "\x1b[6n"
SCROLL_DOWN = "D"
CURSOR_UP, CURSOR_DOWN, CURSOR_FORWARD, CURSOR_BACK = ["[%s" for char in 'ABCD']
ERASE_REST_OF_LINE = "[K"
ERASE_LINE = "[2K"


### Produce simple functions for all escape sequences

def produce_convenience_function(name, seq):
    def func(out_stream):
        out_stream.write(seq)
    func.__name__ = name.lower()
    return func

for name, value in globals().items():
    if name.upper() == name:
        globals()[name.lower()] = produce_convenience_function(name, value)

### Overwrite some of these with more intelligent versions

def produce_cursor_sequence(char):
    """
    Returns a method that issues a cursor control sequence.
    """
    def func(n=1, out_stream=None):
        assert out_stream is not None
        if n: out_stream.write("[%d%s" % (n, char))
    return func

up, down, forward, back = [produce_cursor_sequence(c) for c in 'ABCD']
fwd = forward

### Higher level stuff

def retrying_read(in_stream):
    while True:
        try:
            return in_stream.read(1)
        except IOError:
            logging.debug('read interrupted, retrying')

def get_screen_position(in_stream, out_stream, in_buffer):
    """Returns the terminal (row, column) of the cursor"""
    query_cursor_position(out_stream)
    resp = ''
    while True:
        c = retrying_read(in_stream)
        resp += c
        m = re.search('(?P<extra>.*)\x1b\[(?P<row>\\d+);(?P<column>\\d+)R', resp)
        if m:
            row = int(m.groupdict()['row'])
            col = int(m.groupdict()['column'])
            in_buffer.extend(list(m.groupdict()['extra']))
            return (row, col)


class TCPartialler(object):
    """Returns terminal control functions partialed for stream returned by
    stream_getter on att lookup"""
    def __init__(self, in_stream_getter, out_stream_getter, in_buffer_getter):
        self.in_stream_getter = in_stream_getter
        self.out_stream_getter = out_stream_getter
        self.in_buffer_getter = in_buffer_getter

    def __getattr__(self, att):
        func = globals()[att]
        arg_names = inspect.getargspec(func).args
        kwargs = {k[:-7]: getattr(self, k)() for k in self.__dict__.keys() if k[:-7] in arg_names}
        return functools.partial(globals()[att], **kwargs)

if __name__ == '__main__':
    for k in globals().keys():
        print k

    import cStringIO
    fake = cStringIO.StringIO()
    t = TCPartialler(lambda: fake)
    t.scroll_down()
    fake.seek(0)
    print repr(fake.read())

