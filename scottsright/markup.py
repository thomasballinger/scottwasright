r"""Marked up text for the terminal

text should only be marked up with characteristics that don't change the number
of characters (uppercase is fine - spaces between characters is not)

Ideally these objects can be processed like normal strings

Limited to 

Use something like colorama for Windows output? Skip for now

Similar to https://github.com/kennethreitz/clint/blob/master/clint/textui/colored.py

str: printable (and marked up) text in terminal - minimal amount of markup?
repl: representation of tree structure
getitem: array and farray representation
len: length of version
iteration?

Buildable from escape codes
Buildable from array and farry
Buildable from simple init
Buildable by combining into tree structure

which is the true internal representation?
Probably the array one, can build a tree for repr with cool tree combinators!
No, probably the terminal escape one


What to do on unclosed (uncleared) escape code input?
Close it! Shouldn't be called on just an initial section!


>>> r = Fmt(r'ab\x1b[31mcd\x1b[0m')
>>> r
Red("error message")
>>> c = r + Blue("!")
>>> c
Fmt(Red("error message"), Blue("!"))
>>> str(c)
"""

import termformat
import termformatconstants

class Fmt(object):
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
    pass



if __name__ == '__main__':
    pass #import doctest; doctest.testmod()
