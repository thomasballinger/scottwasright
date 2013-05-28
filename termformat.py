import numpy
import StringIO

def write_from_arrays(array, farray, fhandle, row, columns):
    r"""Write to fhandle from array using farray for row and columns

    >>> a = numpy.array([['a', 'b', 'c', 'd', ' '], ['q', 'w', 'e', 'r', 't']])
    >>> fa = numpy.array([[[0,0,0], [0,0,0], [31,0,0], [31,0,0], [0,0,0]], [[0,0,0], [32,0,0], [33,0,0], [33,0,0], [34,0,0]]])
    >>> f = StringIO.StringIO()
    >>> write_from_arrays(a, fa, f, 0, slice(0, 5))
    >>> f.seek(0); f.read()
    'ab\x1b[31mcd\x1b[0m '
    """
    text = formatted_text(array[row][columns], farray[row][columns])
    fhandle.write(text)

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
            for attr, use in zip(range(1, 9), reversed([bool(int(x)) for x in ('0' * 8 + bin(attrs)[2:])[-8:]])):
                if use:
                    text += fmt_str % attr
        text += char

        text_list.append(text)

    return ''.join(text_list) + (RESET if prev_format != [0, 0, 0] else '')

if __name__ == '__main__':
    from termformatconstants import *
    #import doctest; doctest.testmod()
    #s = formatted_text('hello', numpy.array([[0,0,0], [31,0,0], [32,0,0], [0,0,0], [0,0,0]]))
    #print repr(s)
    #print s
    s = formatted_text('hello', numpy.array([[0,0,0], [RED,0,0], [GREEN,40,0], [0,0, BOLD | DARK | UNDERLINE], [0,0,0]])); print s; print repr(s)
    s = formatted_text('hello', numpy.array([[0,0,0], [RED,0,0], [GREEN,40,0], [0,0, UNDERLINE], [0,0,0]])); print s; print repr(s)
    s = formatted_text('hello', numpy.array([[0,0,0], [RED,0,0], [GREEN,40,0], [0,0, BLINK], [0,0,0]])); print s; print repr(s)
