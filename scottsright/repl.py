import traceback
import sys
import re
import logging
import code
from cStringIO import StringIO

from bpython.autocomplete import Autocomplete

import monkeypatch_site
import replpainter as paint
import events
from  fmtstr.fsarray import FSArray
from fmtstr.fmtstr import fmtstr
from manual_readline import char_sequences as rl_char_sequences
from history import History
from abbreviate import substitute_abbreviations

INFOBOX_ONLY_BELOW = True
INDENT_AMOUNT = 4

logging.basicConfig(level=logging.DEBUG, filename='repl.log')

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
        logging.debug("starting init")
        self.current_line = ''
        self.display_lines = [] # lines separated whenever logical line
                                # length goes over what the terminal width
                                # was at the time of original output
        self.logical_lines = [] # this is every line that's been executed;
                                # it gets smaller on rewind
        self.scroll_offset = 0
        self.cursor_offset_in_line = 0
        self.last_key_pressed = None
        self.last_a_shape = (0,0)
        self.done = True
        self.buffer = []

        self.indent_levels = [0]

        self.history = History()
        self.interp = code.InteractiveInterpreter()
        self.completer = Autocomplete(self.interp.locals)
        self.completer.autocomplete_mode = 'simple'

        self.width = None
        self.height = None

    def __enter__(self):
        self.orig_stdin = sys.stdin
        self.orig_stdout = sys.stdout
        self.orig_stderr = sys.stderr

        sys.stdout = StringIO()
        sys.stderr = StringIO()
        return self

    def __exit__(self, *args):
        sys.stdout = self.orig_stdout
        sys.stderr = self.orig_stderr

    def dumb_print_output(self):
        rows, columns = self.height, self.width
        arr, cpos = self.paint()
        arr[cpos[0], cpos[1]] = '~'
        def my_print(msg):
            self.orig_stdout.write(str(msg)+'\n')
        my_print('X'*(columns+8))
        my_print('X..'+('.'*(columns+2))+'..X')
        for line in arr:
            my_print('X...'+(line if line else ' '*len(line))+'...X')
        logging.debug('line:')
        logging.debug(repr(line))
        my_print('X..'+('.'*(columns+2))+'..X')
        my_print('X'*(columns+8))
        return max(len(arr) - rows, 0)

    def dumb_input(self):
        for c in raw_input('>'):
            if c in '/':
                c = '\n'
            self.process_event(c)

    @property
    def current_display_line(self):
        return (">>> " if self.done else "... ") + self.current_line

    def on_backspace(self):
        if 0 < self.cursor_offset_in_line == len(self.current_line) and self.current_line.count(' ') == len(self.current_line) == self.indent_levels[-1]:
            self.indent_levels.pop()
            self.cursor_offset_in_line = self.indent_levels[-1]
            self.current_line = self.current_line[:self.indent_levels[-1]]
        elif self.cursor_offset_in_line == len(self.current_line) and self.current_line.endswith(' '*INDENT_AMOUNT):
            #dumber version
            self.cursor_offset_in_line = self.cursor_offset_in_line - 4
            self.current_line = self.current_line[:-4]
        else:
            self.cursor_offset_in_line = max(self.cursor_offset_in_line - 1, 0)
            self.current_line = (self.current_line[:max(0, self.cursor_offset_in_line)] +
                                 self.current_line[self.cursor_offset_in_line+1:])

    def on_enter(self):
        self.cursor_offset_in_line = 0
        self.logical_lines.append(self.current_line)
        self.history.on_enter(self.current_line)
        self.display_lines.extend(paint.display_linize(self.current_display_line, self.width))
        output, err, self.done, indent = self.push(self.current_line)
        if output:
            self.display_lines.extend(sum([paint.display_linize(line, self.width) for line in output.split('\n')], []))
        if err:
            self.display_lines.extend([fmtstr(line, 'red') for line in sum([paint.display_linize(line, self.width) for line in err.split('\n')], [])])
        self.current_line = ' '*indent
        self.cursor_offset_in_line = len(self.current_line)

    def on_tab(self):
        cw = self.current_word
        if cw and self.completer.matches:
            self.current_word = self.completer.matches[0]
        elif self.current_line.count(' ') == len(self.current_line):
            for _ in range(INDENT_AMOUNT):
                self.add_normal_character(' ')

    def on_rewind(self):
        if len(self.logical_lines) < 1:
            return
        just_rewound = self.logical_lines.pop()
        old_logical_lines = self.logical_lines
        self.logical_lines = []
        self.display_lines = []
        self.history.clear_history_before_rewind()

        self.done = True
        self.interp = code.InteractiveInterpreter()
        self.completer = Autocomplete(self.interp.locals)
        self.completer.autocomplete_mode = 'simple'
        self.buffer = []

        for line in old_logical_lines:
            self.current_line = line
            self.on_enter()
        self.history.set_just_rewound(just_rewound)
        self.cursor_offset_in_line = 0
        self.current_line = ''

    def process_event(self, e):
        """Returns True if shutting down, otherwise mutates state of Repl object"""
        #logging.debug("processing event %r", e)
        if isinstance(e, events.WindowChangeEvent):
            logging.debug('window change to %d %d', e.width, e.height)
            self.width, self.height = e.width, e.height
            return
        self.last_key_pressed = e
        if e in rl_char_sequences:
            self.cursor_offset_in_line, self.current_line = rl_char_sequences[e](self.cursor_offset_in_line, self.current_line)
        elif e in self.history.char_sequences:
            self.cursor_offset_in_line, self.current_line = self.history.char_sequences[e](self.cursor_offset_in_line, self.current_line)
        elif e == "":
            raise KeyboardInterrupt()
        elif e == "":
            logging.debug('ctrl-d; returning true')
            return True
        elif e == '': # backspace
            self.on_backspace()
        elif e in ("\n", "\r"):
            self.on_enter()
        elif e == "" or e == "":
            pass #dunno what these are, but they screw things up #TODO find out
        elif e == '\t': #tab
            self.on_tab()
        elif e == '':
            self.on_rewind()
        else:
            self.add_normal_character(e)

    @property
    def current_word(self):
        words = re.split(r'([\w_][\w0-9._]*)', self.current_line)
        chars = 0
        cw = None
        for word in words:
            chars += len(word)
            if chars == self.cursor_offset_in_line and word and word.count(' ') == 0:
                cw = word
        if cw and re.match(r'^[\w_][\w0-9._]*$', cw):
            return cw

    @current_word.setter
    def current_word(self, value):
        # current word means word cursor is at the end of, so delete from cursor back to [ .] assert self.current_word
        pos = self.cursor_offset_in_line - 1
        while pos > -1 and self.current_line[pos] not in tuple(' :()'):
            pos -= 1
        start = pos + 1; del pos
        self.current_line = self.current_line[:start] + value + self.current_line[self.cursor_offset_in_line:]
        self.cursor_offset_in_line = start + len(value)

    def add_normal_character(self, char):
        self.current_line = (self.current_line[:self.cursor_offset_in_line] +
                             char +
                             self.current_line[self.cursor_offset_in_line:])
        self.cursor_offset_in_line += 1
        self.cursor_offset_in_line, self.current_line = substitute_abbreviations(self.cursor_offset_in_line, self.current_line)
        #TODO deal with characters that take up more than one space? do we care?

    def push(self, line):
        """Run a line of code.

        Return ("for stdout", "for_stderr", finished?)
        """
        self.buffer.append(line)
        indent = len(re.match(r'[ ]*', line).group())
        self.indent_levels = [l for l in self.indent_levels if l < indent] + [indent]

        if line.endswith(':'):
            self.indent_levels.append(indent + INDENT_AMOUNT)
        elif line and line.count(' ') == len(self.current_line) == self.indent_levels[-1]:
            self.indent_levels.pop()
        elif line and ':' not in line and line.strip().startswith(('return', 'pass', 'raise', 'yield')):
            self.indent_levels.pop()
        out_spot = sys.stdout.tell()
        err_spot = sys.stderr.tell()
        logging.debug('running %r in interpreter', self.buffer)
        unfinished = self.interp.runsource('\n'.join(self.buffer))
        sys.stdout.seek(out_spot)
        sys.stderr.seek(err_spot)
        out = sys.stdout.read()
        err = sys.stderr.read()
        if unfinished and not err:
            logging.debug('unfinished - line added to buffer')
            return (None, None, False, self.indent_levels[-1])
        else:
            logging.debug('finished - buffer cleared')
            self.buffer = []
            if err:
                self.indent_levels = [0]
            return (out[:-1], err[:-1], True, self.indent_levels[-1])

    def paint(self, about_to_exit=False):
        """Returns an array of min_height or more rows and width columns, plus cursor position"""
        width, min_height = self.width, self.height
        arr = FSArray(0, width) #, 'on_blue') ## default background color
        current_line_start_row = len(self.display_lines) - self.scroll_offset

        history = paint.paint_history(current_line_start_row, width, self.display_lines)
        arr[:history.shape[0],:history.shape[1]] = history

        current_line = paint.paint_current_line(min_height, width, self.current_display_line)
        arr[current_line_start_row:current_line_start_row + current_line.shape[0],
            0:current_line.shape[1]] = current_line

        if current_line.shape[0] > min_height:
            return arr, (0, 0) # short circuit, no room for infobox

        lines = paint.display_linize(self.current_display_line+'X', width)
                                       # extra character for space for the cursor
        cursor_row = current_line_start_row + len(lines) - 1
        cursor_column = (self.cursor_offset_in_line + len(self.current_display_line) - len(self.current_line)) % width

        if self.current_word and not about_to_exit: # since we don't want the infobox then
            visible_space_above = history.shape[0]
            visible_space_below = min_height - cursor_row
            info_max_rows = max(visible_space_above, visible_space_below)
            info = self.info(width-2, info_max_rows)
            infobox = paint.paint_infobox(info_max_rows, width, info)
            logging.debug('infobox:')
            logging.debug(infobox)

            if visible_space_above >= infobox.shape[0] and not INFOBOX_ONLY_BELOW:
                assert len(infobox.shape) == 2, repr(infobox.shape)
                arr[current_line_start_row - infobox.shape[0]:current_line_start_row, 0:infobox.shape[1]] = infobox
            else:
                arr[cursor_row + 1:cursor_row + 1 + infobox.shape[0], 0:infobox.shape[1]] = infobox

        self.last_a_shape = arr.shape
        logging.debug(arr)
        return arr, (cursor_row, cursor_column)

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

    def info(self, width, height):
        cw = self.current_word
        if cw:
            try:
                self.completer.complete(cw, 0)
            except:
                e = traceback.format_exception(*sys.exc_info())
                return '\n'.join(e)
            else:
                if not self.completer.matches:
                    return 'no matches'
                matches = sorted(set(self.completer.matches))
                word_width = max(len(m) for m in matches)
                words_per_line = ((width+1) / (word_width+1))
                suggestions = '\n'.join(
                    [' '.join(
                        [m+(' '*(word_width - len(m)))
                         for m in matches[i*words_per_line:(i+1)*words_per_line]])
                     for i in range((len(matches) / words_per_line) + 1)])
                return str(cw) + '\n' + suggestions
        else:
            return 'no current word:\n' + repr(re.split(r'([\w_][\w0-9._]+)', self.current_line))

def test():
    with Repl() as r:
        r.width = 50
        r.height = 10
        while True:
            scrolled = r.dumb_print_output()
            r.scroll_offset += scrolled
            r.dumb_input()

if __name__ == '__main__':
    test()
