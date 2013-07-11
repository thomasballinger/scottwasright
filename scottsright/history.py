"""implementations of readline control sequences to do with history

Implementing these similar to how they're done in bpython:
    * never modifying previous history entries
    * always appending the executed line
in the order of description at http://www.bigsmoke.us/readline/shortcuts
"""


CHAR_SEQUENCES = {}

def on(seq):
    def add_to_seq_handler(func):
        CHAR_SEQUENCES[seq] = func.__name__
        return func
    return add_to_seq_handler

line_with_cursor_at_end = lambda line: (len(line), line)

class History(object):
    def __init__(self):
        self.logical_lines = []
        self.history_index = 0
        self.filter_line = ''
        self.char_sequences = {seq: getattr(self, handler)
                               for seq, handler in CHAR_SEQUENCES.items()}

    def use_history_index(self):
        current_line = self.logical_lines[-self.history_index]
        return line_with_cursor_at_end(current_line)


    @on('')
    @on('[A')
    def prev_line_in_history(self, cursor_offset, current_line):
        if cursor_offset != len(current_line):
            return line_with_cursor_at_end(current_line)
        else:
            if self.history_index == 0:
                self.filter_line = current_line
            if len(self.logical_lines) == 0:
                return cursor_offset, current_line
            self.history_index = (self.history_index % len(self.logical_lines)) + 1
            return self.use_history_index()

    @on('')
    @on('[B')
    def next_line_in_history(self, cursor_offset, current_line):
        if self.history_index == 0:
            return cursor_offset, current_line
        else:
            self.history_index -= 1
            if self.history_index == 0:
                return line_with_cursor_at_end(self.filter_line)
            return self.use_history_index()

    @on('.')
    def back_to_current_line_in_history(self, cursor_offset, current_line):
        raise NotImplementedError()

    def on_enter(self, line):
        self.history_index = 0
        self.logical_lines.append(line)
