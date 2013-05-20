
def rewindable_iter(iterable, history=1):
    """Rewindable iterator

    >>> rw = rewindable_iter(range(5))
    >>> rw.next(), rw.next(), rw.send(1), rw.next()
    (0, 1, None, 1)
    >>> for x in rw: x
    2
    3
    4

    >>> rw = rewindable_iter(range(5))
    >>> rw.next(), rw.send(2)
    Traceback (most recent call last):
    IndexError: history length set too low to rewind iterator

    >>> rw = rewindable_iter(range(5))
    >>> rw.next(), rw.next(), rw.send(2)
    Traceback (most recent call last):
    IndexError: history length set too low to rewind iterator

    >>> rw = rewindable_iter(range(5), 2)
    >>> rw.next(), rw.send(2)
    Traceback (most recent call last):
    IndexError: not enough history to rewind iterator

    >>> rw = rewindable_iter(range(5), 2)
    >>> rw.next(), rw.next(), rw.send(1), rw.send(1), rw.next()
    (0, 1, None, None, 0)
    """
    i = iter(iterable)
    results = []
    backtrack = 0
    rewind = None
    while True:
        if rewind is not None:
            backtrack += rewind
            if backtrack > history:
                raise IndexError("history length set too low to rewind iterator")
            if backtrack > len(results):
                raise IndexError("not enough history to rewind iterator")
            rewind = None
            rewind = yield None
            continue
        if backtrack > 0:
            rewind = yield results[-backtrack]
            backtrack -= 1
        else:
            r = i.next()
            results.append(r)
            rewind = yield r
        while len(results) > history: results.pop(0)

def safe_zip(*rewindable_iterators):
    """On StopIteration, save partial output

    >>> a = rewindable_iter(range(4))
    >>> b = rewindable_iter(range(2))
    >>> for x, y in safe_zip(a, b):
    ...    pass
    >>> a.next()
    2

    """
    output = []
    while True:
        new_list = []
        for i in range(len(rewindable_iterators)):
            try:
                new_list.append(rewindable_iterators[i].next())
            except StopIteration:
                for iterator in rewindable_iterators[:i]:
                    iterator.send(1)
                return output
        output.append(tuple(new_list))


def test_zip():
    """Dummy function to test normal zip

    Zip will consume an extra element of a iterators on the last pass through
    that come before the iterator which raises StopIteration.

    >>> a = iter(range(4))
    >>> b = iter(range(2))
    >>> for x, y in zip(a, b):
    ...    pass
    >>> a.next()
    3
    """
    pass

import doctest
doctest.testmod()
