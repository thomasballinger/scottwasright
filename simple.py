"""

* maybe scroll down all the way immediately? Have an option for that maybe?

"""


import sys
import os
import numpy

from autoextend import AutoExtending

class Repl(object):
    """

    Renders 2d arrays of characters

    takes in:
     -terminal dimensions and change events
     -keystrokes
     -scroll down events
     -initial cursor position


    Geometry information gets passed around, while REPL information is state
      one the object
"""

    def __init__(self):
        self.current_line = ''
        self.logical_lines = []
        self.display_lines = [] # lines separated whenever logical line
                                # length goes over what the terminal width
                                # was at the time of original output

        self.initial_row = None
        self.scroll_offset = 0
        self.cursor_offset_in_line = 0
        self.last_key_pressed = None

    def dumb_paint(self):
        a = self.paint(self.rows, self.columns)
        print 'X'*(self.columns+4)
        print 'X'+(' '*(self.columns+2))+'X'
        for line in a:
            print 'X '+(''.join([line[i] for i in range(len(line))]) if line[0] else ' '*self.columns)+' X'
        print 'X'+(' '*(self.columns+2))+'X'
        print 'X'*(self.columns+4)
        return max(len(a) - self.rows, 0)

    def dumb_input(self):
        for c in raw_input('>'):
            if c in '/':
                c = '\n'
            self.process_char(c)

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

    def display_linize(self, msg, columns=None):
        if columns is None: columns = self.columns
        display_lines = ([msg[start:end]
                    for start, end in zip(
                        range(0, len(msg), columns),
                        range(columns, len(msg)+columns, columns))]
                if self.current_line else [''])
        return display_lines

    # All paint functions should
    # * return an array of the width they were asked for
    # * return an array not larger than the height they were asked for

    def paint_history(self, rows, columns):
        lines = []
        for r, line in zip(range(rows), self.display_lines[-rows:]):
            lines.append((line+' '*1000)[:columns])
        return numpy.array([list(s) for s in lines]) if lines else numpy.array([[]])

    def paint_current_line(self, rows, columns):
        lines = self.display_linize(self.current_line, columns)
        return numpy.array([(list(line)+[' ']*columns)[:columns] for line in lines])

    def paint_infobox(self, msg, rows, columns):
        #TODO actually truncate infobox if necessary
        lines = msg.split('\n')
        width = max([len(line) for line in lines])
        output_lines = []
        output_lines.extend(self.display_linize('+'+'-'*width+'+', columns))
        for line in lines:
            output_lines.extend(self.display_linize('|'+line+' '*(width - len(line))+'|', columns))
        output_lines.extend(self.display_linize('+'+'-'*width+'+', columns))
        return numpy.array([(list(x)+[' ']*columns)[:columns] for x in output_lines][:rows])

    def paint(self, rows, columns):
        #TODO make an automatically extending 2d array
        a = AutoExtending(rows, columns)

        first_line_we_own = max(0, self.initial_row - self.scroll_offset)
        current_line_start_row = self.initial_row - self.scroll_offset + len(self.display_lines)

        history = self.paint_history(current_line_start_row, columns)
        print 'current line start row', current_line_start_row
        print 'history.shape', history.shape
        a[first_line_we_own:history.shape[0],0:history.shape[1]] = history

        current_line = self.paint_current_line(rows, columns)
        a[current_line_start_row:current_line_start_row + current_line.shape[0],
            0:current_line.shape[1]] = current_line

        if current_line.shape[0] > rows:
            return a

        space_above = history.shape[0]
        space_below = rows - current_line_start_row - current_line.shape[0]
        infobox = self.paint_infobox(repr(self), max(space_above, space_below), columns)
        if space_above >= infobox.shape[0]:
            a[current_line_start_row - infobox.shape[0]:current_line_start_row, 0:infobox.shape[1]] = infobox
        else:
            a[current_line_start_row+current_line.shape[0]:current_line_start_row+current_line.shape[0]+infobox.shape[0], 0:infobox.shape[1]] = infobox
        #self.paint_cursor()

        return a

    def run(self):
        while True:
            print self.paint(10, 20)
            c = self.get_char()
            self.process_char(c)

    def window_change_event(self):
        print 'window changed!'

    def __repr__(self):
        s = ''
        s += '<TerminalWrapper\n'
        s += " cursor_offset_in_line:" + repr(self.cursor_offset_in_line) + '\n'
        s += " num display lines:" + repr(len(self.display_lines)) + '\n'
        s += " last key presed:" + repr(self.last_key_pressed) + '\n'
        s += " lines scrolled down:" + repr(self.scroll_offset) + '\n'
        s += '>'
        return s

if __name__ == '__main__':
    r = Repl()
    r.initial_row = 0
    r.columns = 50
    r.rows = 20
#TODO Don't pass around the screen size, just pass around how big to render things - so
#     display_linize() doesn't need to be passed number of columns
    while True:
        scrolled = r.dumb_paint()
        r.scroll_offset += scrolled
        r.dumb_input()
