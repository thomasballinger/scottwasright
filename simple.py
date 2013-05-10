"""

* Let's do our own line wrapping, so we can remember how the line was wrapped
    so when we replace it under an informational window, we have enough
    information to do so
* what to do about scrolling up? On keypress, scroll all the way back down?

* maybe scroll down all the way immediately? Have an option for that maybe?
"""


import sys
import os
import re
import tty

def up(n=1): sys.stdout.write("[%dA" % n)
def down(n=1): sys.stdout.write("[%dB" % n)
def fwd(n=1): sys.stdout.write("[%dC" % n)
def back(n=1): sys.stdout.write("[%dD" % n)
def erase_end_of_line(): sys.stdout.write("[K")

QUERY_CURSOR_POSITION = "\x1b[6n"

class TerminalWrapper(object):
    def __init__(self):
        self.current_line = ''
        self.stdin_buffer = []
        self.times_scrolled = 0

    def get_char(self):
        """Use this in case a query was issued and input
        had to be read in to answer it, but another character or so
        was read in at that time as well"""
        if self.stdin_buffer:
            return self.stdin_buffer.pop(0)
        else:
            return sys.stdin.read(1)

    def get_pos(self):
        sys.stdout.write(QUERY_CURSOR_POSITION)
        resp = ''
        while True:
            c = sys.stdin.read(1)
            resp += c
            m = re.search('\x1b\[(?P<row>\\d+);(?P<column>\\d+)R', resp)
            if m:
                row = int(m.groupdict()['row'])
                col = int(m.groupdict()['column'])
                return (row, col)

    def set_pos(self, (row, col)):
        print "[%d;%dH" % (row, col),

    def scroll_down(self):
        print "D",
        self.scrolls += 1

    def get_screen_size(self):
        orig = self.get_pos()
        fwd(10000)
        down(10000)
        size = self.get_pos()
        self.set_pos(orig)
        return size

    def our_space_on_screen(self):
        """Returns the rows currently on screen that we can safely write to
        because we know what goes underneath

        These lines are exactly as they appeared on screen at the time, not to do
        with logical lines.

        getting lines_above and lines_below seems useful - if neither is enough
        for an infobox, we should scroll down to make room
        """
        pos = self.get_pos()
        lines_above = pos[0] - self.start_row
        size = self.get_screen_size()
        lines_below = size[0] - pos[0]
        return lines_above, lines_below

    def info_screen(self, msg):
        """msg should not have lines longer than current width of screen"""
        #TODO implement a max height these things can be
        orig = self.get_pos()
        lines = msg.split('\n')
        width = max([len(line) for line in lines])
        info_height = len(lines)+2
        above, below = self.our_space_on_screen()
        if above >= info_height:
            up(info_height)
        elif below >= info_height:
            down(1)
        else:
            for _ in range(info_height - below):
                self.scroll_down()
                up(1)
            down(1)

        back(1000)
        sys.stdout.write('+'+'-'*width+'+')
        for line in lines:
            down(1)
            back(1000)
            sys.stdout.write('|'+line+' '*(width - len(line))+'|')
        down(1)
        back(1000)
        sys.stdout.write('+'+'-'*width+'+')
        back(1000)
        self.set_pos(orig)

    def rewrite_our_lines(self):
        """Rewrites saved lines to screen as they were before"""

    def write_line(self):
        """Writes a new line, wrapping behavior imitating a normal write"""
        #width = 
        pass

    def process_char(self, char):
        if char == '':
            back(1)
            self.current_line = self.current_line[:-1]
        elif char == "":
            raise KeyboardInterrupt()
        else:
            self.current_line += char
            pass

    def _run(self):
        tty.setraw(sys.stdin)
        self.start_row, _ = self.get_pos()
        while True:
            c = self.get_char()
            self.process_char(c)
            self.our_space_on_screen()
            self.info_screen(repr(self))
            back(1000)
            sys.stdout.write(self.current_line)
            erase_end_of_line()

    def __repr__(self):
        s = ''
        s += '<TerminalWrapper\n'
        s += " rows above/below:" + repr(self.our_space_on_screen()) + '\n'
        s += " cursor_pos:" + repr(self.get_pos()) + '\n'
        s += '>'
        return s

    def run(self):
        try:
            self._run()
        finally:
            os.system('reset')

if __name__ == '__main__':
    TerminalWrapper().run()
