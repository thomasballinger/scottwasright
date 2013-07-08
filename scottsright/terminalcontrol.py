"""
Terminal control sequences

see: https://en.wikipedia.org/wiki/ANSI_escape_code#CSI_codes

inspired by
https://github.com/gwk/gloss/blob/master/python/gloss/io/cs.py
"""

import functools

import logging

QUERY_CURSOR_POSITION = "\x1b[6n"
SCROLL_DOWN = "D"
CURSOR_UP, CURSOR_DOWN, CURSOR_FORWARD, CURSOR_BACK = ["[%s" for char in 'ABCD']
ERASE_REST_OF_LINE = "[K"
ERASE_LINE = "[2K"


### Produce simple functions for all escape sequences

def produce_convenience_function(name, seq):
    def func(stream):
        stream.write(seq)
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
    def func(stream, n=1):
        if n: stream.write("[%d%s" % (n, char))
    return func

up, down, forward, back = [produce_cursor_sequence(c) for c in 'ABCD']
fwd = forward

class TCPartialler(object):
    """Returns terminal control functions partialed for stream returned by
    stream_getter on att lookup"""
    def __init__(self, stream_getter):
        self.stream_getter = stream_getter
    def __getattr__(self, att):
        return functools.partial(globals()[att], self.stream_getter())

def retrying_read(stream):
    while True:
        try:
            return stream.read(1)
        except IOError:
            logging.debug('read interrupted, retrying')

if __name__ == '__main__':
    for k in globals().keys():
        print k

    import cStringIO
    fake = cStringIO.StringIO()
    t = TCPartialler(lambda: fake)
    t.scroll_down()
    fake.seek(0)
    print repr(fake.read())

