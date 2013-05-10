"""



* keep track of how many lines belong to us, so we can store and overwrite them
* figure out how to display a box of arbitrary text best within the space we have
    (usually put it underneath, at least at first)
* on ctr-d fix up the terminal not to have this any more before exit
* deal with line wrapping however is appropriate
* keep internal state for what is where

"""

import sys
import tty
import os
import curses
import termios

#curses.initscr()
#curses.echo(0)


def up(n=1): print "[%dA" % n,
def down(n=1): print "[%dB" % n,
def fwd(n=1): print "[%dC" % n,
def back(n=1): print "[%dD" % n,
def get_pos():
    #todo make this much more robust - it should happen automatically I guess
    # we can't count on only reading what we expect to read, we might get something else initially
    print "[6n"
    resp = ''
    while True:
        c = sys.stdin.read(1)
        if c == 'R':
            break
        resp += c
    row = int(resp[2:resp.index(';')])
    col = int(resp[resp.index(';')+1:])
    return (row, col)

def set_pos((row, col)):
    print "[%d;%dH" % (row, col),

def at_bottom():
    r, c = get_pos()
    down()
    r2, c2 = get_pos()
    if r == r2:
        return True
    else:
        up()
        return False

def rect_above(msg):
    lines = msg.split('\n')
    up(len(lines)+2)
    width = max([len(line) for line in lines])
    back(1000)
    sys.stdout.write('+'+'-'*width+'+'+' '*50)
    for line in lines:
        down(1)
        back(1000)
        sys.stdout.write('|'+line+' '*(width - len(line))+'|'+' '*50)
    down(1)
    back(1000)
    sys.stdout.write('+'+'-'*width+'+'+' '*50)
    back(1000)

class CLI(object):
    def __init__(self):
        self.current_line = ''
        self.old_lines = []
        self.cursor_column = 1
        self.last_key_pressed = None
        self.scrolls = 0

    def scroll_down(self):
        print "D",
        self.scrolls += 1

    def process_key(self, char):
        self.last_key_pressed = char
        if char == '': # delete key
            self.current_line = self.current_line[:-1]
            self.cursor_column = max(1, self.cursor_column-1)
        elif char == """""" or char == "\n" or char == "\r": # return key, processed, or ?
            self.old_lines.append(self.current_line)
            self.current_line = ''
            self.cursor_column = 1
            if at_bottom():
                self.scroll_down()
            else:
                self.cursor_row += 1
        elif char == "":
            raise KeyboardInterrupt()
        else:
            self.current_line += char
            self.cursor_column = self.cursor_column + 1

    def paint(self):
        top = self.start_row - self.scrolls
        if top >= 1:
            to_display = self.old_lines[:]
        else:
            to_display = self.old_lines[self.scrolls-self.start_row:]
        up(1000)
        back(1000)
        for line in to_display:
            print line
            back(1000)
            down(1)
        back(1000)
        sys.stdout.write(self.current_line)
        print ' '*100,
        rect_above('\n'.join([self.current_line]*2+[repr((self.cursor_row, self.cursor_column))]+[repr(self.last_key_pressed)]))
        set_pos((self.cursor_row, self.cursor_column))

    def run(self):
        #tty.setcbreak(sys.stdin)
        tty.setraw(sys.stdin)
        self.start_row, _ = get_pos()
        rect_above("Hello there\nMy name is Tom!")
        import os
        self.cursor_row, self.cursor_column = get_pos()
        while True:
            c = sys.stdin.read(1)
            self.process_key(c)
            self.paint()

if __name__ == '__main__':
    try:
        CLI().run()
    finally:
        os.system('reset')

