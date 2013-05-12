"""

* Let's do our own line wrapping, so we can remember how the line was wrapped
    so when we replace it under an informational window, we have enough
    information to do so
* what to do about scrolling up? On keypress, scroll all the way back down?

* maybe scroll down all the way immediately? Have an option for that maybe?

* good deal of redraw optimizations to be made - nothing should disappear

* Vertial window size change: always try to scroll down for each move down
  * these scrolls shouldn't do anything if history is at top of window
  * on vertical smaller, scroll down iff we need the space
  * actually, on scroll up, perhaps th eright thing will just happen?
  * eventually catch the change window events, for now just compare size between paints
"""


import sys
import os
import re
import tty
import functools
import signal



QUERY_CURSOR_POSITION = "\x1b[6n"

def move_cursor_direction(char, n=1):
    if n: sys.stdout.write("[%d%s" % (n, char))
up, down, fwd, back = [functools.partial(move_cursor_direction, char) for char in 'ABCD']

def erase_rest_of_line(): sys.stdout.write("[K")

class TerminalWrapper(object):
    """The model here is of a much larger screen, so scrolling can be ignored
    by the user of this api"""

    def __init__(self):
        self.current_line = ''
        self.stdin_buffer = []
        self.scroll_offset = 0
        self.logical_lines = []

        # lines separated whenever logical line length goes over
        #   what the terminal width was at the time of original output
        self.display_lines = []

        self.initial_screen_row = None
        self.pos = [0, 1]
        self.last_key_pressed = None

    def get_char(self):
        """Use this in case a query was issued and input
        had to be read in to answer it, but another character or so
        was read in at that time as well"""
        if self.stdin_buffer:
            return self.stdin_buffer.pop(0)
        else:
            return sys.stdin.read(1)

    def get_screen_position(self):
        """Returns the terminal (row, column) of the cursor"""
        sys.stdout.write(QUERY_CURSOR_POSITION)
        resp = ''
        while True:
            c = sys.stdin.read(1)
            resp += c
            m = re.search('(?P<extra>.*)\x1b\[(?P<row>\\d+);(?P<column>\\d+)R', resp)
            if m:
                row = int(m.groupdict()['row'])
                col = int(m.groupdict()['column'])
                self.stdin_buffer.extend(list(m.groupdict()['extra']))
                return (row, col)

    def set_screen_pos(self, (row, col)):
        sys.stdout.write("[%d;%dH" % (row, col))

    def scroll_down(self):
        sys.stderr.write("D")
        self.scroll_offset += 1

    def get_screen_size(self):
        orig = self.get_screen_position()
        fwd(10000)
        down(10000)
        size = self.get_screen_position()
        self.set_screen_pos(orig)
        return size

    def rows_above_below(self):
        """Returns the rows currently on screen that we can safely write to
        because we know what goes underneath

        These lines are exactly as they appeared on screen at the time, not to do
        with logical lines.

        getting lines_above and lines_below seems useful - if neither is enough
        for an infobox, we should scroll down to make room
        """
        pos = self.get_screen_position()
        lines_above = pos[0] - self.initial_screen_row + self.scroll_offset
        size = self.get_screen_size()
        lines_below = size[0] - pos[0]
        return lines_above, lines_below

    def info_screen(self, msg):
        """msg should not have lines longer than current width of screen"""
        #TODO implement a max height these things can be
        # Currently assumes cursor is on the output line
        back(1000)
        orig = self.get_screen_position()
        lines = msg.split('\n')
        width = max([len(line) for line in lines])
        info_height = len(lines)+2
        above, below = self.rows_above_below()
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
        erase_rest_of_line()
        for line in lines:
            down(1)
            back(1000)
            sys.stdout.write('|'+line+' '*(width - len(line))+'|')
            erase_rest_of_line()
        down(1)
        back(1000)
        sys.stdout.write('+'+'-'*width+'+')
        erase_rest_of_line()
        back(1000)
        self.set_screen_pos(orig)

    def rewrite_our_lines(self):
        """Rewrites saved lines to screen as they were before"""

    def write_line(self):
        """Writes a new line, wrapping behavior imitating a normal write"""
        #width = 
        pass

    def process_char(self, char):
        self.last_key_pressed = char
        if char == '':
            self.pos[1] = max(self.pos[1] - 1, 1)
            self.current_line = self.current_line[:-1]
        elif char == "":
            raise KeyboardInterrupt()
        elif char == "":
            os.system('reset')
            sys.exit()
        elif char == """""" or char == "\n" or char == "\r": # return key, processed, or ?
            self.logical_lines.append(self.current_line)
            self.display_lines.append(self.current_line) #TODO proper display line handling
            self.current_line = ''
            self.pos[0] += 1 #TODO num display lines for current_line
            self.pos[1] = 1
            if self.pos[0] + self.initial_screen_row - self.scroll_offset > self.get_screen_size()[0]:
                self.scroll_down()
        elif char == "" or char == "":
            pass #dunno what these are, but they screw things up
        else:
            self.current_line += char
            self.pos[1] += 1 #TODO handle wrapping
        #TODO deal with characters that take up more than one space

    def paint(self):
        self.set_screen_pos((self.pos[0] + self.initial_screen_row - self.scroll_offset, self.pos[1]))
        top_line_we_own = self.initial_screen_row - self.scroll_offset
        for i, line in zip(range(top_line_we_own, top_line_we_own + len(self.display_lines)), self.display_lines):
            if i > 0:
                self.set_screen_pos((i, 0))
                sys.stdout.write(line)
                erase_rest_of_line()
        back(1000)
        for i in range(100):
            down()
            erase_rest_of_line()
        self.set_screen_pos((self.pos[0] + self.initial_screen_row - self.scroll_offset, 0))
        sys.stdout.write(self.current_line)
        erase_rest_of_line()
        self.info_screen(repr(self))
        fwd(len(self.current_line))

    def _run(self):
        tty.setraw(sys.stdin)
        self.initial_screen_row, _ = self.get_screen_position()
        signal.signal(signal.SIGWINCH, lambda signum, frame: self.window_change_event())
        while True:
            self.paint()
            c = self.get_char()
            self.process_char(c)

    def window_change_event(self):
        print 'window changed!'

    def __repr__(self):
        s = ''
        s += '<TerminalWrapper\n'
        s += " rows above/below:" + repr(self.rows_above_below()) + '\n'
        s += " cursor_pos:" + repr(self.get_screen_position()) + '\n'
        s += " pos:" + repr(self.pos) + '\n'
        s += " last key presed:" + repr(self.last_key_pressed) + '\n'
        s += " lines scrolled down:" + repr(self.scroll_offset) + '\n'
        s += '>'
        return s

    def run(self):
        try:
            self._run()
        finally:
            os.system('reset')

if __name__ == '__main__':
    TerminalWrapper().run()
