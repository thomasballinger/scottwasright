from scottsright.terminal import Terminal
from scottsright.repl import Repl
from scottsright.terminalcontrol import TCPartialler
import sys

def main():
    with TCPartialler() as tc:
        with Terminal(tc) as t:
            with Repl() as r:
                rows, columns = tc.get_screen_size()
                r.width = columns
                r.height = rows
                while True:
                    result = r.process_event(tc.get_event())
                    array, cursor_pos = r.paint()
                    scrolled = t.render_to_terminal(array, cursor_pos)
                    r.scroll_offset += scrolled
                    if result:
                        sys.exit()

main()
