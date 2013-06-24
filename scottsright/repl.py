import numpy
import sys
import traceback
from cStringIO import StringIO

from autoextend import AutoExtending
from manual_readline import char_sequences as rl_char_sequences

class Repl(object):
    """

    takes in:
     -terminal dimensions and change events
     -keystrokes
     -number of scroll downs necessary to render array
     -initial cursor position
    outputs:
     -2D array to be rendered

    Geometry information gets passed around, while REPL information is state
      on the object

    TODO change all "rows" to "height" iff rows is a number
    (not if it's an array of the rows)
"""

    def __init__(self):
        self.current_line = ''
        self.logical_lines = []
        self.display_lines = [] # lines separated whenever logical line
                                # length goes over what the terminal width
                                # was at the time of original output

        self.scroll_offset = 0
        self.cursor_offset_in_line = 0
        self.last_key_pressed = None
        self.last_a_shape = (0,0)
        self.done = True

        self.display_line_width = None # the width to which to wrap the current line

        self.orig_stdin = sys.stdin
        self.orig_stdout = sys.stdout
        self.orig_stderr = sys.stderr

        #TODO mock out stdin as necessary
        sys.stdout = StringIO()
        sys.stderr = StringIO()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.cleanup()

    def cleanup(self):
        sys.stderr.seek(0)
        errors = sys.stderr.read()
        sys.stdin = self.orig_stdin
        sys.stdout = self.orig_stdout
        sys.stderr = self.orig_stderr
        sys.stderr.write(errors)

    def dumb_print_output(self, rows, columns):
        a, cpos = self.paint(rows, columns)
        a[cpos[0], cpos[1]] = '~'
        def my_print(*messages):
            self.orig_stdout.write(' '.join(str(msg) for msg in messages)+'\n')
        my_print('X'*(columns+8)+'\n')
        my_print('X  '+(' '*(columns+2))+'  X')
        for line in a:
            my_print('X   '+(''.join([line[i] if line[i] else ' ' for i in range(len(line))]) if line[0] else ' '*columns)+'   X')
        my_print('X  '+(' '*(columns+2))+'  X')
        my_print('X'*(columns+8))
        return max(len(a) - rows, 0)

    def dumb_input(self):
        for c in raw_input('>'):
            if c in '/':
                c = '\n'
            self.process_char(c)

    @property
    def current_display_line(self):
        return (">>> " if self.done else "... ") + self.current_line

    def process_char(self, char):
        """Returns True if shutting down, otherwise mutates state of Repl object"""
        self.last_key_pressed = char
        if char in rl_char_sequences:
            self.cursor_offset_in_line, self.current_line = rl_char_sequences[char](self.cursor_offset_in_line, self.current_line)
        elif char == "":
            raise KeyboardInterrupt()
        elif char == "":
            return True
        elif char == "\n" or char == "\r": # return key, processed, or ?
            self.cursor_offset_in_line = 0
            self.logical_lines.append(self.current_line)
            self.display_lines.extend(self.display_linize(self.current_display_line, self.display_line_width))
            output, err, self.done = self.push(self.current_line)
            if output:
                self.display_lines.extend(self.display_linize(output, self.display_line_width))
            if err:
                self.display_lines.extend(sum([self.display_linize(line, self.display_line_width) for line in err.split('\n') if line.split()], []))
            self.current_line = ''
        elif char == "" or char == "":
            pass #dunno what these are, but they screw things up #TODO find out
        else:
            self.current_line = (self.current_line[:self.cursor_offset_in_line] +
                                 char +
                                 self.current_line[self.cursor_offset_in_line:])
            self.cursor_offset_in_line += 1
        #TODO deal with characters that take up more than one space? do we care?

    def push(self, msg):
        """Returns output, error output, and whether command is complete"""
        try:
            out = repr(eval(msg))
            return (out, None, True)
        except:
            err = traceback.format_exc()
            return (None, err, True)

    def display_linize(self, msg, columns):
        display_lines = ([msg[start:end]
                            for start, end in zip(
                                range(0, len(msg), columns),
                                range(columns, len(msg)+columns, columns))]
                        if msg else [''])
        return display_lines

    # All paint functions should
    # * return an array of the width they were asked for
    # * return an array not larger than the height they were asked for

    def paint_history(self, rows, columns):
        lines = []
        for r, line in zip(range(rows), self.display_lines[-rows:]):
            lines.append((line+' '*1000)[:columns])
        r = numpy.array([list(s) for s in lines]) if lines else numpy.zeros((0,0), dtype=numpy.character)
        assert r.shape[0] <= rows, repr(r.shape)+' '+repr(rows)
        assert r.shape[1] <= columns
        return r

    def paint_current_line(self, rows, columns):
        lines = self.display_linize(self.current_display_line, columns)
        return numpy.array([(list(line)+[' ']*columns)[:columns] for line in lines])

    def paint_infobox(self, msg, rows, columns):
        #TODO actually truncate infobox if necessary
        if not (rows and columns):
            return numpy.zeros((0,0), dtype=numpy.character)
        lines = msg.split('\n')
        width = max([len(line) for line in lines])
        output_lines = []
        output_lines.extend(self.display_linize('+'+'-'*width+'+', columns))
        for line in lines:
            output_lines.extend(self.display_linize('|'+line+' '*(width - len(line))+'|', columns))
        output_lines.extend(self.display_linize('+'+'-'*width+'+', columns))
        r = numpy.array([(list(x)+[' ']*(width+2))[:width+2] for x in output_lines][:rows])
        assert len(r.shape) == 2
        return r

    def paint(self, min_height, width, about_to_exit=False):
        """Returns an array of min_height or more rows and width columns, plus cursor position"""
        a = AutoExtending(0, width)
        current_line_start_row = len(self.display_lines) - self.scroll_offset

        history = self.paint_history(current_line_start_row, width)
        a[:history.shape[0],:history.shape[1]] = history

        current_line = self.paint_current_line(min_height, width)
        a[current_line_start_row:current_line_start_row + current_line.shape[0],
            0:current_line.shape[1]] = current_line

        if current_line.shape[0] > min_height:
            return a # short circuit, no room for infobox

        lines = self.display_linize(self.current_display_line+'X', width)
        cursor_row = current_line_start_row + len(lines) - 1
        cursor_column = (self.cursor_offset_in_line + len(self.current_display_line) - len(self.current_line)) % width

        if not about_to_exit: # since we don't want the infobox then
            visible_space_above = history.shape[0]
            visible_space_below = min_height - cursor_row
            infobox = self.paint_infobox(repr(self), max(visible_space_above, visible_space_below), width)

            #if visible_space_above >= infobox.shape[0]:
            if False: # never paint over text
                assert len(infobox.shape) == 2, repr(infobox.shape)
                a[current_line_start_row - infobox.shape[0]:current_line_start_row, 0:infobox.shape[1]] = infobox
            else:
                a[cursor_row + 1:cursor_row + 1 + infobox.shape[0], 0:infobox.shape[1]] = infobox

        self.last_a_shape = a.shape
        return a, (cursor_row, cursor_column)

    def window_change_event(self):
        print 'window changed!'

    def __repr__(self):
        s = ''
        s += '<TerminalWrapper\n'
        s += " size of last array rendered" + repr(self.last_a_shape) + '\n'
        s += " cursor_offset_in_line:" + repr(self.cursor_offset_in_line) + '\n'
        s += " num display lines:" + repr(len(self.display_lines)) + '\n'
        s += " last key presed:" + repr(self.last_key_pressed) + '\n'
        s += " lines scrolled down:" + repr(self.scroll_offset) + '\n'
        s += '>'
        return s

def test():
    with Repl() as r:
        r.display_line_width = 50
        while True:
            scrolled = r.dumb_print_output(20, 50)
            r.scroll_offset += scrolled
            r.dumb_input()

if __name__ == '__main__':
    test()
