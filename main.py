from scottsright.terminal import Terminal
from scottsright.coderepl import CodeRepl as Repl
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
                    array, cursor_pos = r.paint(rows, columns, about_to_exit=True)
                    t.render_to_terminal(array, cursor_pos)
                    sys.exit()

main()
