"""Marked up text for the terminal

Ideally these objects can be processed like normal strings

str: printable text in terminal
repl: representation of tree structure
getitem: array and farray representation


Buildable from array and farry
Buildable from simple init
Buildable by combining into tree structure
Buildable from escape codes?

which is the true internal representation?
Probably the array one, can build a tree for repr with cool tree combinators!


>>> r = Red('error message')
>>> r
Red("error message")
>>> c = r + Blue("!")
>>> c
Fmt(Red("error message"), Blue("!"))
>>> str(c)
'h\x1b[31me\x1b[0m\x1b[32mll\x1b[0mo!'
"""
import termformat
import termformatconstants

class FormattedLine(object):
    """
    text with formatting information

    contains no newlines
    """
    def __init__(self, fg=0, bg=0, attrs=0):
        self.contents = contents
        self.fg = fg
        self.bg = bg
        self.attrs = attrs

    def to_array_and_farray(self):
        pass

    def __repr__(self):
        return 1

class CompoundFormattedLine(FormattedLine):



if __name__ == '__main__':
    pass #import doctest; doctest.testmod()
