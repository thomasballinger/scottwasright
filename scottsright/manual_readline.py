"""implementations of simple readline control sequences

just the ones that fit the model of transforming the current line
and the cursor location
in the order of description at http://www.bigsmoke.us/readline/shortcuts"""

from friendly import NotImplementedError
char_sequences = {}

INDENT = 4

def on(seq):
    def add_to_char_sequences(func):
        char_sequences[seq] = func
        return func
    return add_to_char_sequences

@on('[D')
@on('')
def left_arrow(cursor_offset, line):
    return max(0, cursor_offset - 1), line

@on('[C')
@on('')
def right_arrow(cursor_offset, line):
    return min(len(line), cursor_offset + 1), line

@on('')
def beginning_of_line(cursor_offset, line):
    return 0, line

@on('')
def end_of_line(cursor_offset, line):
    return len(line), line

@on('f')
def forward_word(cursor_offset, line):
    raise NotImplementedError()

@on('b')
def back_word(cursor_offset, line):
    raise NotImplementedError()

@on('[3~')
def delete(cursor_offset, line):
    return (cursor_offset,
            line[:cursor_offset] + line[cursor_offset+1:])

@on('')
@on('')
def backspace(cursor_offset, line):
    if cursor_offset == 0:
        return cursor_offset, line
    if not line[:cursor_offset].strip(): #if just whitespace left of cursor
        front_white = len(line[:cursor_offset]) - len(line[:cursor_offset].lstrip())
        to_delete = ((front_white - 1) % INDENT) + 1
        return cursor_offset - to_delete, line[:to_delete]
    return (cursor_offset - 1,
            line[:cursor_offset - 1] + line[cursor_offset:])

@on('')
def delete_from_cursor_back(cursor_offset, line):
    return 0, line[cursor_offset:]

@on('')
def delete_from_cursor_forward(cursor_offset, line):
    return cursor_offset, line[:cursor_offset]

@on('d')
def delete_rest_of_word(cursor_offset, line):
    raise NotImplementedError()

@on('')
def delete_word_to_cursor(cursor_offset, line):
    raise NotImplementedError()

@on('')
def yank_prev_killed_text(cursor_offset, line):
    raise NotImplementedError()

@on('y')
def yank_prev_prev_killed_text(cursor_offset, line):
    raise NotImplementedError()

@on('')
def transpose_character_before_cursor(cursor_offset, line):
    raise NotImplementedError()

@on('t')
def transpose_word_before_cursor(cursor_offset, line):
    raise NotImplementedError()

if __name__ == '__main__':
    from pprint import pprint
    #pprint(char_sequences)
    import doctest; doctest.testmod()

