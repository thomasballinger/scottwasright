"""
Terminal control sequences

see: https://en.wikipedia.org/wiki/ANSI_escape_code#CSI_codes

inspired by
https://github.com/gwk/gloss/blob/master/python/gloss/io/cs.py
"""




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

for name, value in locals().items():
    if name.upper() == name:
        locals()[name.lower()] = produce_convenience_function(name, value)

### Overwrite some of these with more intelligent versions

def produce_cursor_sequence(char):
    """
    Returns a method that issues a cursor control sequence.
    """
    def func(self, n=1):
        if n: self.out_stream.write("[%d%s" % (n, char))
    return func

if __name__ == '__main__':
    for k in locals().keys():
        print k

