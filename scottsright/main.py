import terminal
import repl
import sys

def main():
    r = repl.Repl()
    with terminal.Terminal(sys.stdin, sys.stdout) as t:
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
