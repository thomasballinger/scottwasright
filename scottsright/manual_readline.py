
char_sequences = {}

def on(seq):
    def add_to_char_sequences(func):
        char_sequences[seq] = func
        return func
    return add_to_char_sequences

@on('[D')
@on('')
@on('\x02')
def left_arrow(cursor_offset, line):
    return max(0, cursor_offset - 1), line

if __name__ == '__main__':
    print repr(char_sequences)
