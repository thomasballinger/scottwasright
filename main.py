from scottsright.terminal import Terminal
from scottsright.repl import Repl
import sys

def main():
    with Terminal(sys.stdin, sys.stdout) as t:
        with Repl() as r:
            rows, columns = t.get_screen_size()
            r.display_line_width = columns
            while True:
                array, cursor_pos = r.paint(rows, columns)
                scrolled = t.render_to_terminal(array, cursor_pos)
                r.scroll_offset += scrolled
                if r.process_char(t.get_char()):
                    array, cursor_pos = r.paint(rows, columns)
                    t.render_to_terminal(array, cursor_pos)
                    sys.exit()

main()
