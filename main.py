import simple
import fresh
import os
import sys

def safe_run(f):
    try:
        f()
    finally:
        os.system('reset')

def main():
    r = simple.Repl()
    t = fresh.Terminal(sys.stdin, sys.stdout)
    rows, columns = t.get_screen_size()
    r.display_line_width = columns
    r.initial_row, _ = t.get_screen_position()
    while True:
        array, cursor_pos = r.paint(rows, columns)
        scrolled = t.render_to_terminal(array, cursor_pos)
        r.scroll_offset += scrolled
        r.process_char(t.get_char())

safe_run(main)

