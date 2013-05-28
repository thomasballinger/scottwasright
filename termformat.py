import numpy

def formatted_text(character_list, format_array):
    r"""Returns text formatted according to the format_array

    >>> formatted_text('hello', numpy.array([[0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0]]))
    'hello'
    >>> formatted_text('hello!', numpy.array([[0,0,0], [31,0,0], [32,0,0], [32,0,0], [0,0,0], [0,0,0]]))
    'h\x1b[31me\x1b[0m\x1b[32mll\x1b[0mo!'

    """
    assert len(character_list) == len(format_array)
    assert format_array.shape[1] == 3
    RESET = '\033[0m'

    prev_format = [0, 0, 0]

    text_list = []

    for char, f in zip(character_list, format_array):
        text = ''
        if prev_format == list(f):
            text_list.append(char)
            continue

        color, on_color, attrs = f
        if color == on_color == attrs == 0:
            text_list.append(RESET + char)
            prev_format = [color, on_color, attrs]
            continue

        text = RESET if prev_format != [0, 0, 0] else ''
        prev_format = list(f)

        fmt_str = '\033[%dm'
        if color != 0:
            text += fmt_str % color
        if on_color != 0:
            text += fmt_str % on_color
        if attrs != 0:
            # something stupid like below?
            for attr, use in zip(range(1, 9), [bool(int(x)) for x in ('0' * 10 + bin(12)[2:])[-10:]]):
                if use:
                    text += fmt_str % attr
        text += char

        text_list.append(text)

    return ''.join(text_list) + (RESET if prev_format != [0, 0, 0] else '')

if __name__ == '__main__':
    import doctest; doctest.testmod()
    #s = formatted_text('hello', numpy.array([[0,0,0], [31,0,0], [32,0,0], [0,0,0], [0,0,0]]))
    #print s
    #print repr(s)
