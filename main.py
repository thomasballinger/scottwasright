from scottsright.terminal import Terminal
from scottsright.repl import Repl
import sys

def main():
    with Terminal(sys.stdin, sys.stdout) as t:
        with Repl() as r:
            rows, columns = t.get_screen_size()
            r.width = columns
            r.height = rows
            while True:
                result = r.process_event(t.get_event())
                array, cursor_pos = r.paint()
                scrolled = t.render_to_terminal(array, cursor_pos)
                r.scroll_offset += scrolled
                if result:
                    sys.exit()

main()
