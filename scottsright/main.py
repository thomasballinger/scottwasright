from scottsright.terminal import Terminal
from scottsright.repl import Repl
from scottsright.terminalcontrol import TerminalController

def main():
    with TerminalController() as tc:
        with Terminal(tc) as term:
            with Repl() as repl:
                rows, columns = tc.get_screen_size()
                repl.width = columns
                repl.height = rows
                while True:
                    try:
                        repl.process_event(tc.get_event())
                    except SystemExit:
                        array, cursor_pos = repl.paint(about_to_exit=True)
                        term.render_to_terminal(array, cursor_pos)
                        raise
                    else:
                        array, cursor_pos = repl.paint()
                        scrolled = term.render_to_terminal(array, cursor_pos)
                        repl.scroll_offset += scrolled
main()
