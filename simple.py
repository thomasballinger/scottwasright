"""

* maybe scroll down all the way immediately? Have an option for that maybe?

"""


import sys
import os
import tty
import signal

class Repl(object):
    """

    Renders 2d arrays of characters

    takes in:
     -terminal dimensions and change events
     -keystrokes
     -scroll down events
     -initial cursor position
"""

    def __init__(self):
        self.current_line = ''
        self.logical_lines = []
        self.display_lines = [] # lines separated whenever logical line
                                # length goes over what the terminal width
                                # was at the time of original output

        self.initial_screen_row = None
        self.scroll_offset = 0
        self.cursor_offset_in_line = 0
        self.last_key_pressed = None

    def dumb_paint(self):
        for line in self.display_lines:
            print line
        for line in self.display_linize(self.current_line):
            print line

    def dumb_input(self):
        for c in raw_input('>'):
            if c in '/':
                c = '\n'
            self.process_char(c)

    @property
    def current_line_start_screen_row(self):
        """Should only be called when cursor is at a resting place"""

    def rewrite_our_lines(self):
        """Rewrites saved lines to screen as they were before"""

    def write_line(self):
        """Writes a new line, wrapping behavior imitating a normal write"""
        #width = 
        pass

    def process_char(self, char):
        self.last_key_pressed = char
        if char == '':
            self.cursor_offset_in_line = max(self.cursor_offset_in_line - 1, 0)
            self.current_line = self.current_line[:-1]
        elif char == "":
            raise KeyboardInterrupt()
        elif char == "":
            os.system('reset')
            sys.exit()
        elif char == "\n" or char == "\r": # return key, processed, or ?
            self.cursor_offset_in_line = 0
            self.logical_lines.append(self.current_line)
            self.display_lines.extend(self.display_linize(self.current_line))
            self.current_line = ''
        elif char == "":
            self.scroll_up()
        elif char == "":
            self.scroll_down()
        elif char == "" or char == "":
            pass #dunno what these are, but they screw things up
        else:
            self.current_line += char
            self.cursor_offset_in_line += 1
        #TODO deal with characters that take up more than one space

    def display_linize(self, msg):
        columns = self.columns
        display_lines = ([self.current_line[start:end]
                    for start, end in zip(
                        range(0, len(self.current_line), columns),
                        range(columns, len(self.current_line)+columns, columns))]
                if self.current_line else [''])
        return display_lines

    def formatted_info(self, min_dimensions=None):
        if min_dimensions is None:
            pass
        else:
            raise NotImplementedError("currently relying on info being small enough")
        lines = self.info_msg.split('\n')
        #TODO do smarter formatting, inc. line wrapping
        width = max([len(line) for line in lines])
        output_lines = []
        output_lines.append('+'+'-'*width+'+')
        for line in lines:
            output_lines.append('|'+line+' '*(width - len(line))+'|')
        output_lines.append('+'+'-'*width+'+')
        return output_lines

    def paint_history(self):
        rows, columns = self.get_screen_size()
        first_screen_row_to_render = max(1, self.initial_screen_row - self.scroll_offset)
        screen_row = first_screen_row_to_render
        display_line_for_screen_line = lambda line: line - self.initial_screen_row + self.scroll_offset
        while 0 <= display_line_for_screen_line(screen_row) < len(self.display_lines):
            self.set_screen_pos((screen_row, 1))
            sys.stdout.write(self.display_lines[display_line_for_screen_line(screen_row)][:columns])
            screen_row += 1

    def paint_current_line(self):
        rows, columns = self.get_screen_size()
        self.set_screen_pos((self.initial_screen_row - self.scroll_offset + len(self.display_lines), 1))

        def write_line(line):
            back(1000)
            sys.stdout.write(line)
            erase_rest_of_line()

        lines = self.display_linize(self.current_line)
        line = lines[0]
        write_line(line)
        for line in lines[1:]:
            self.force_down()
            write_line(line)
        if len(line) == columns:
            self.force_down()
            erase_line()
        cur_row, cur_col = self.get_screen_position()
        #for _ in range(rows - cur_row):
        #    down()
            #erase_line()

    def paint_cursor(self):
        rows, columns = self.get_screen_size()
        cursor_screen_row = self.initial_screen_row - self.scroll_offset + len(self.display_lines) + (self.cursor_offset_in_line / columns)
        for _ in range(cursor_screen_row - rows):
            self.force_down()
        cursor_screen_column = 1 + self.cursor_offset_in_line % columns
        self.set_screen_pos((cursor_screen_row, cursor_screen_column))

    def paint_infobox(self):
        """

        * figure out max space we get to render infobox above current line
        * crop infobox to that size
        * if space, render above, else scroll down and render below
        """

        rows, columns = self.get_screen_size()
        lines = self.formatted_info()
        space_above = self.initial_screen_row - self.scroll_offset + len(self.display_lines) + 1 - max(1, self.initial_screen_row - self.scroll_offset)
        space_below = rows - (self.initial_screen_row - self.scroll_offset + len(self.display_lines) + (len(self.current_line) + 1) / columns)
        if len(lines) > space_above:
            pass
        else:
            for i, line in enumerate(lines):
                self.set_screen_pos((i, 0))
                sys.stdout.write(line)
                erase_rest_of_line()


    def paint(self):
        """Scrolls to new position if necessary, then paints everything
        
        * how many rows will current line take up, plus the cursor?
        * how many rows will infobox take up?
          * is there room for it above?
          * if not, needs to go below
        * based on where on screen the current line shows up, how many rows of history can we show above it?
        * Scroll down as much is necessary for new rendering

        """
        #TODO Don't repaint everything every time! Don't even repaint the current line if not necessary
        self.info_msg = repr(self)

        self.paint_history()
        #self.paint_current_line()
        self.paint_infobox()
        self.paint_cursor()


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
        s += " cursor_pos:" + repr(self.get_screen_position()) + '\n'
        s += " cursor_offset_in_line:" + repr(self.cursor_offset_in_line) + '\n'
        s += " num display lines:" + repr(len(self.display_lines)) + '\n'
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
    r = Repl()
    while True:
        r.columns = 14
        r.dumb_paint()
        r.dumb_input()
