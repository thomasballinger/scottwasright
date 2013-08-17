import sys
import os
import re
import logging
import code
import threading
import Queue
import time
from cStringIO import StringIO

from bpython.autocomplete import Autocomplete, SUBSTRING, FUZZY, SIMPLE
from bpython.repl import Repl as BpythonRepl, Interaction as BpythonInteraction
from bpython.config import Struct, loadini, default_config_path
from bpython.formatter import BPythonFormatter
from pygments import format
from bpython import importcompletion
from bpython import translations
translations.init()
from bpython.translations import _

import sitefix; sitefix.monkeypatch_quit()
import replpainter as paint
import events
from fmtstr.fsarray import FSArray
from fmtstr.fmtstr import fmtstr, FmtStr
from fmtstr.bpythonparse import parse as bpythonparse
from manual_readline import char_sequences as rl_char_sequences
from abbreviate import substitute_abbreviations

INFOBOX_ONLY_BELOW = True
INDENT_AMOUNT = 4

logging.basicConfig(level=logging.DEBUG, filename='repl.log', datefmt='%M:%S')

class StatusBar(BpythonInteraction):
    """StatusBar and Interaction for Repl

    Passing of control back and forth between calls that use interact api
    (notify, confirm, file_prompt) like bpython.Repl.write2file and events
    on the main thread happens via those calls and self.wait_for_request_or_notify.

    Calling one of these three is required for the main thread to regain control!

    This is probably a terrible idea, and better would be rewriting this
    functionality in a evented or callback style, but trying to integrate
    bpython.Repl code.
    """
    #TODO Remove dependence on bpython.Repl, it's more complicated than it's worth!
    def __init__(self, initial_message='', permanent_text=""):
        self._current_line = ''
        self.cursor_offset_in_line = 0
        self.in_prompt = False
        self.in_confirm = False
        self.prompt = ''
        self._message = initial_message
        self.message_start_time = time.time()
        self.message_time = 3
        self.permanent_text = permanent_text
        self.response_queue = Queue.Queue(maxsize=1)
        self.request_or_notify_queue = Queue.Queue()

    @property
    def has_focus(self):
        return self.in_prompt or self.in_confirm

    def message(self, msg):
        self.message_start_time = time.time()
        self._message = msg

    def _check_for_expired_message(self):
        if self._message and time.time() > self.message_start_time + self.message_time:
            self._message = ''

    def process_event(self, e):
        """Returns True if shutting down"""
        assert self.in_prompt or self.in_confirm
        if e in rl_char_sequences:
            self.cursor_offset_in_line, self._current_line = rl_char_sequences[e](self.cursor_offset_in_line, self._current_line)
        elif e == "":
            raise KeyboardInterrupt()
        elif e == "":
            raise SystemExit()
        elif self.in_prompt and e in ("\n", "\r"):
            self.response_queue.put(self._current_line)
            self.escape()
        elif self.in_confirm:
            if e in ('y', 'Y'):
                self.response_queue.put(True)
            else:
                self.response_queue.put(False)
            self.escape()
        elif e == "\x1b":
            self.response_queue.put(False)
            self.escape()
        else: # add normal character
            #TODO factor this out, same in both process_event methods
            self._current_line = (self._current_line[:self.cursor_offset_in_line] +
                                 e +
                                 self._current_line[self.cursor_offset_in_line:])
            self.cursor_offset_in_line += 1

    def escape(self):
        """unfocus from statusbar, clear prompt state, wait for notify call"""
        self.wait_for_request_or_notify()
        self.in_prompt = False
        self.in_confirm = False
        self.prompt = ''
        self._current_line = ''

    @property
    def current_line(self):
        self._check_for_expired_message()
        if self.in_prompt:
            return self.prompt + self._current_line
        if self.in_confirm:
            return self.prompt
        if self._message:
            return self._message
        return self.permanent_text

    def wait_for_request_or_notify(self):
        try:
            r = self.request_or_notify_queue.get(True, 1)
        except Queue.Empty:
            raise Exception('Main thread blocked because task thread not calling back')
        return r

    # interaction interface - should be called from other threads
    def notify(self, msg, n=3):
        self.message_time = n
        self.message(msg)
        self.request_or_notify_queue.put(msg)
    # below Really ought to be called from threads other than the mainloop because they block
    def confirm(self, q):
        """Expected to return True or False, given question prompt q"""
        self.prompt = q
        self.in_confirm = True
        self.request_or_notify_queue.put(q)
        return self.response_queue.get()
    def file_prompt(self, s):
        """Expected to return a file name, given """
        self.prompt = s
        self.in_prompt = True
        self.request_or_notify_queue.put(s)
        r = self.response_queue.get()
        return r

class Repl(BpythonRepl):
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
        interp = code.InteractiveInterpreter()
        config = Struct()
        loadini(config, default_config_path())
        config.autocomplete_mode = SIMPLE # only one implemented currently
        self.status_bar = StatusBar(_('welcome to bpython'))
        logging.debug("starting parent init")
        super(Repl, self).__init__(interp, config)
        self.interact = self.status_bar # overwriting, for bpython.Repl to use

        self._current_line = ''
        self.current_formatted_line = fmtstr('')
        self.display_lines = [] # lines separated whenever logical line
                                # length goes over what the terminal width
                                # was at the time of original output
        self.history = [] # this is every line that's been executed;
                                # it gets smaller on rewind
        self.display_buffer = []
        self.formatter = BPythonFormatter(config.color_scheme)
        self.scroll_offset = 0
        self.cursor_offset_in_line = 0
        self.done = True


        self.paste_mode = False

        self.width = None
        self.height = None
        self.start_background_tasks()

    ## Required by bpython.repl.Repl
    def current_line(self):
        """Returns the current line"""
        return self._current_line
    def echo(self, msg, redraw=True):
        """
        Notification that redrawing the current line is necessary (we dont' generally
        care, since we always redraw the whole screen)

        Supposed to parse and echo a formatted string with appropriate attributes. It
        srings. It won't update the screen if it's reevaluating the code (as it
        does with undo)."""
        logging.debug("echo called with %r" % msg)
    def cw(self):
        """Returns the "current word", based on what's directly left of the cursor.
        examples inclue "socket.socket.metho" or "self.reco" or "yiel" """
        return self.current_word
    @property
    def cpos(self):
        "many WATs were had - it's the pos from the end of the line back"""
        return len(self._current_line) - self.cursor_offset_in_line
    def reprint_line(self, lineno, tokens):
        logging.debug("calling reprint line with %r %r", lineno, tokens)
        self.display_buffer[lineno] = bpythonparse(format(tokens, self.formatter))
    def reevaluate(self):
        """bpython.Repl.undo calls this"""
        #TODO other implementations have a enter no-history method, could do
        # that instead of clearing history and getting it rewritten
        old_logical_lines = self.history
        self.history = []
        self.display_lines = []

        self.done = True # this keeps the first prompt correct
        self.interp = code.InteractiveInterpreter()
        self.completer = Autocomplete(self.interp.locals, self.config)
        self.completer.autocomplete_mode = 'simple'
        self.buffer = []
        self.display_buffer = []
        self.highlighted_paren = None

        for line in old_logical_lines:
            self._current_line = line
            self.set_formatted_line()
            self.on_enter()
        self.cursor_offset_in_line = 0
        self._current_line = ''
    def getstdout(self):
        logging.debug('in getstdout')
        lines = self.lines_for_display + [self.current_formatted_line]
        s = '\n'.join([x.s if isinstance(x, FmtStr) else s
                       for x in lines]) if lines else ''
        logging.debug('got display lines')
        return s

    ## wrappers for super functions so I can add descriptive docstrings
    def tokenize(self, s, newline=False):
        """Tokenizes a line of code, returning what that line should look like,
        with side effects:

        - reads self.cpos to see what parens should be highlighted
        - reads self.buffer to see what came before the passed in line
        - sets self.highlighted_paren to (buffer_lineno, tokens_for_that_line) for buffer line
            that should replace that line to unhighlight it
        - calls reprint_line with a buffer's line's tokens and the buffer lineno that has changed
            iff that line is the not the current line
        """
        return super(Repl, self).tokenize(s, newline)

    ## Our own functions
    def unhighlight_paren(self):
        """set self.display_buffer after """
        if self.highlighted_paren is not None:
            lineno, saved_tokens = self.highlighted_paren
            if lineno == len(self.display_buffer):
                # then this is the current line, so don't worry about it
                return
            self.highlighted_paren = None
            logging.debug('trying to unhighlight a paren on line %r', lineno)
            logging.debug('with these tokens: %r', saved_tokens)
            new = bpythonparse(format(saved_tokens, self.formatter))
            self.display_buffer[lineno][:len(new)] = new

    @property
    def lines_for_display(self):
        return self.display_lines + self.display_buffer_lines

    @property
    def display_buffer_lines(self):
        lines = []
        #logging.debug('display_buffer:')
        #logging.debug(self.display_buffer)
        for display_line in self.display_buffer:
            display_line = (self.ps2 if lines else self.ps1) + display_line
            for line in paint.display_linize(display_line, self.width):
                lines.append(line)
        return lines

    def __enter__(self):
        self.orig_stdout = sys.stdout
        self.orig_stderr = sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()
        return self

    def __exit__(self, *args):
        sys.stderr.seek(0)
        s = sys.stderr.read()
        self.orig_stderr.write(s)
        sys.stdout = self.orig_stdout
        sys.stderr = self.orig_stderr

    @property
    def current_display_line(self):
        return (self.ps1 if self.done else self.ps2) + self.current_formatted_line

    def start_background_tasks(self):
        t = threading.Thread(target=self.importcompletion_thread)
        t.daemon = True
        t.start()

    def importcompletion_thread(self):
        """quick tasks we want to do bits of during downtime"""
        while importcompletion.find_coroutine(): # returns None when fully initialized
            pass

    def on_enter(self):
        self.cursor_offset_in_line = 10000
        self.unhighlight_paren()
        self.set_formatted_line()

        self.rl_history.append(self._current_line)
        self.rl_history.last()
        self.history.append(self._current_line)
        output, err, self.done, indent = self.push(self._current_line)
        if output:
            self.display_lines.extend(sum([paint.display_linize(line, self.width) for line in output.split('\n')], []))
        if err:
            self.display_lines.extend([fmtstr(line, 'red') for line in sum([paint.display_linize(line, self.width) for line in err.split('\n')], [])])
        self._current_line = ' '*indent
        self.cursor_offset_in_line = len(self._current_line)

    def only_whitespace_left_of_cursor(self):
        """returns true if all characters on current line before cursor are whitespace"""
        return self._current_line[:self.cursor_offset_in_line].strip()

    def on_tab(self, back=False):
        """Do something on tab key
        taken from bpython.cli

        Does one of the following:
        1) add space to move up to the next %4==0 column
        2) complete the current word with characters common to all completions and
        3) select the first or last match
        4) select the next or previous match if already have a match
        """
        logging.debug('self.matches: %r', self.matches)
        if not self.only_whitespace_left_of_cursor():
            front_white = (len(self._current_line[:self.cursor_offset_in_line]) -
                len(self._current_line[:self.cursor_offset_in_line].lstrip()))
            to_add = 4 - (front_white % INDENT_AMOUNT)
            for _ in range(to_add):
                self.add_normal_character(' ')
            return

        # get the (manually typed or common-sequence completed from manually typed) current word
        if self.matches_iter:
            cw = self.matches_iter.current_word
        else:
            self.complete(tab=True) #TODO why do we call this here?
            if not self.config.auto_display_list and not self.list_win_visible:
                return True #TODO why?
            cw = self.current_string() or self.current_word
            if not cw:
                return

        # check to see if we can expand the current word
        cseq = os.path.commonprefix(self.matches)
        expanded_string = cseq[len(cw):]
        if expanded_string:
            self.current_word = cw + expanded_string #asdf
            self.matches_iter.update(cseq, self.matches)
            return

        if self.matches:
            self.current_word = (self.matches_iter.previous()
                                 if back else self.matches_iter.next())

    def add_normal_character(self, char):
        assert len(char) == 1
        self._current_line = (self._current_line[:self.cursor_offset_in_line] +
                             char +
                             self._current_line[self.cursor_offset_in_line:])
        self.cursor_offset_in_line += 1
        self.cursor_offset_in_line, self._current_line = substitute_abbreviations(self.cursor_offset_in_line, self._current_line)
        #TODO deal with characters that take up more than one space? do we care?

    def process_event(self, e):
        """Returns True if shutting down, otherwise mutates state of Repl object"""
        #logging.debug("processing event %r", e)
        if isinstance(e, events.WindowChangeEvent):
            logging.debug('window change to %d %d', e.width, e.height)
            self.width, self.height = e.width, e.height
            return
        if self.status_bar.has_focus:
            return self.status_bar.process_event(e)
        if e in rl_char_sequences:
            self.cursor_offset_in_line, self._current_line = rl_char_sequences[e](self.cursor_offset_in_line, self._current_line)
            self.set_completion()

        # readline history commands
        elif e in ["", "[A"]:
            self.rl_history.enter(self._current_line)
            self._current_line = self.rl_history.back(False)
            self.cursor_offset_in_line = len(self._current_line)
            self.set_completion()
        elif e in ["", "[B"]:
            self.rl_history.enter(self._current_line)
            self._current_line = self.rl_history.forward(False)
            self.cursor_offset_in_line = len(self._current_line)
            self.set_completion()
        #TODO add rest of history commands

        elif e == "":
            raise KeyboardInterrupt()
        elif e == "":
            raise SystemExit()
        elif e in ("\n", "\r"):
            self.on_enter()
            self.set_completion()
        elif e in ["", "", "\x00", "\x11"]:
            pass #dunno what these are, but they screw things up #TODO find out
        elif e == '\t': # tab
            self.on_tab()
        elif e == '[Z': # shift-tab
            self.on_tab(back=True)
        elif e == '':
            self.undo()
            self.set_completion()
        elif e == '\x13': # ctrl-s for save
            t = threading.Thread(target=self.write2file)
            t.daemon = True
            logging.debug('starting write2file thread')
            t.start()
            self.interact.wait_for_request_or_notify()
        elif e == '\x1b[19~': # F8 for pastebin
            t = threading.Thread(target=self.pastebin)
            t.daemon = True
            logging.debug('starting pastebin thread')
            t.start()
            self.interact.wait_for_request_or_notify()
        else:
            self.add_normal_character(e)
            self.set_completion()
        self.set_formatted_line()

    def clean_up_current_line_for_exit(self):
        """Called when trying to exit to prep for final paint"""
        logging.debug('resetting formatted line for exit')
        self.cursor_offset_in_line = -1
        self.unhighlight_paren()
        self.set_formatted_line()

    def set_formatted_line(self):
        self.current_formatted_line = bpythonparse(format(self.tokenize(self._current_line), self.formatter))
        logging.debug(repr(self.current_formatted_line))

    def set_completion(self, tab=False):
        """Update autocomplete info; self.matches and self.argspec"""
        # this method stolen from bpython.cli
        if self.paste_mode:
            return

        if self.list_win_visible and not self.config.auto_display_list:
            self.list_win_visible = False
            self.matches_iter.update(self.current_word)
            return

        if self.config.auto_display_list or tab:
            self.list_win_visible = BpythonRepl.complete(self, tab)

    @property
    def current_word(self):
        words = re.split(r'([\w_][\w0-9._]*[(]?)', self._current_line)
        chars = 0
        cw = None
        for word in words:
            chars += len(word)
            if chars == self.cursor_offset_in_line and word and word.count(' ') == 0:
                cw = word
        if cw and re.match(r'^[\w_][\w0-9._]*[(]?$', cw):
            return cw

    @current_word.setter
    def current_word(self, value):
        # current word means word cursor is at the end of, so delete from cursor back to [ ."']
        pos = self.cursor_offset_in_line - 1
        if pos > -1 and self._current_line[pos] not in tuple(' :)'):
            pos -= 1
        while pos > -1 and self._current_line[pos] not in tuple(' :()\'"'):
            pos -= 1
        start = pos + 1; del pos
        self._current_line = self._current_line[:start] + value + self._current_line[self.cursor_offset_in_line:]
        self.cursor_offset_in_line = start + len(value)

    def push(self, line):
        """Push a line of code onto the buffer, run the buffer

        If the interpreter successfully runs the code, clear the buffer
        Return ("for stdout", "for_stderr", finished?)
        """
        self.buffer.append(line)
        indent = len(re.match(r'[ ]*', line).group())

        if line.endswith(':'):
            indent = max(0, indent + INDENT_AMOUNT)
        elif line and line.count(' ') == len(self._current_line):
            indent = max(0, indent - INDENT_AMOUNT)
        elif line and ':' not in line and line.strip().startswith(('return', 'pass', 'raise', 'yield')):
            indent = max(0, indent - INDENT_AMOUNT)
        out_spot = sys.stdout.tell()
        err_spot = sys.stderr.tell()
        #logging.debug('running %r in interpreter', self.buffer)
        unfinished = self.interp.runsource('\n'.join(self.buffer))
        self.display_buffer.append(bpythonparse(format(self.tokenize(line), self.formatter))) #current line not added to display buffer if quitting
        sys.stdout.seek(out_spot)
        sys.stderr.seek(err_spot)
        out = sys.stdout.read()
        err = sys.stderr.read()

        # easier debugging: save only errors that aren't from this interpreter
        oldstderr = sys.stderr
        sys.stderr = StringIO()
        oldstderr.seek(0)
        sys.stderr.write(oldstderr.read(err_spot))

        if unfinished and not err:
            logging.debug('unfinished - line added to buffer')
            return (None, None, False, indent)
        else:
            logging.debug('finished - buffer cleared')
            self.display_lines.extend(self.display_buffer_lines)
            self.display_buffer = []
            self.buffer = []
            if err:
                indent = 0
            return (out[:-1], err[:-1], True, indent)

    def paint(self, about_to_exit=False):
        """Returns an array of min_height or more rows and width columns, plus cursor position"""

        if about_to_exit:
            self.clean_up_current_line_for_exit()

        width, min_height = self.width, self.height
        show_status_bar = bool(self.status_bar.current_line)
        if show_status_bar:
            min_height -= 1
        arr = FSArray(0, width)
        current_line_start_row = len(self.lines_for_display) - max(0, self.scroll_offset)

        if current_line_start_row < 0: #if current line trying to be drawn off the top of the screen
            #assert True, 'no room for current line: contiguity of history broken!'
            msg = "#<---History contiguity broken by rewind--->"
            arr[0, 0:min(len(msg), width)] = [msg[:width]]

            # move screen back up a screen minus a line
            self.scroll_offset = self.scroll_offset - self.height

            current_line_start_row = len(self.lines_for_display) - max(-1, self.scroll_offset)

            history = paint.paint_history(current_line_start_row - 1, width, self.lines_for_display)
            arr[1:history.height+1,:history.width] = history

            if arr.height <= min_height:
                arr[min_height, 0] = ' ' # force scroll down to hide broken history message
        else:
            history = paint.paint_history(current_line_start_row, width, self.lines_for_display)
            arr[:history.height,:history.width] = history

        current_line = paint.paint_current_line(min_height, width, self.current_display_line)
        arr[current_line_start_row:current_line_start_row + current_line.height,
            0:current_line.width] = current_line

        if current_line.height > min_height:
            return arr, (0, 0) # short circuit, no room for infobox

        lines = paint.display_linize(self.current_display_line+'X', width)
                                       # extra character for space for the cursor
        cursor_row = current_line_start_row + len(lines) - 1
        cursor_column = (self.cursor_offset_in_line + len(self.current_display_line) - len(self._current_line)) % width

        if self.list_win_visible:
            logging.debug('infobox display code running')
            visible_space_above = history.height
            visible_space_below = min_height - cursor_row
            info_max_rows = max(visible_space_above, visible_space_below)
            infobox = paint.paint_infobox(info_max_rows, width, self.matches, self.argspec, self.current_word, self.docstring, self.config)

            if visible_space_above >= infobox.height and not INFOBOX_ONLY_BELOW:
                arr[current_line_start_row - infobox.height:current_line_start_row, 0:infobox.width] = infobox
            else:
                arr[cursor_row + 1:cursor_row + 1 + infobox.height, 0:infobox.width] = infobox
                logging.debug('slamming infobox of shape %r into arr', infobox.shape)

        if show_status_bar and not about_to_exit:
            arr[max(arr.height, min_height), :] = paint.paint_statusbar(1, width, self.status_bar.current_line)
        return arr, (cursor_row, cursor_column)

    ## Debugging shims
    def dumb_print_output(self):
        rows, columns = self.height, self.width
        arr, cpos = self.paint()
        arr[cpos[0], cpos[1]] = '~'
        def my_print(msg):
            self.orig_stdout.write(str(msg)+'\n')
        my_print('X'*(columns+8))
        my_print(' use "/" for enter '.center(columns+8, 'X'))
        my_print(' use "\\" for rewind '.center(columns+8, 'X'))
        my_print(' use "|" to raise an error '.center(columns+8, 'X'))
        my_print(' use "$" to pastebin '.center(columns+8, 'X'))
        my_print(' "~" is the cursor '.center(columns+8, 'X'))
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
            elif c in '\\':
                c = ''
            elif c in '|':
                def r(): raise Exception('real errors should look like this')
                t = threading.Thread(target=r)
                t.daemon = True
                t.start()
            elif c in '$':
                c = '[19~'
            self.process_event(c)

    def __repr__(self):
        s = ''
        s += '<Repl\n'
        s += " cursor_offset_in_line:" + repr(self.cursor_offset_in_line) + '\n'
        s += " num display lines:" + repr(len(self.display_lines)) + '\n'
        s += " lines scrolled down:" + repr(self.scroll_offset) + '\n'
        s += '>'
        return s

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
