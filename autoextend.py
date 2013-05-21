import numpy

class AutoExtending(object):
    """Numpy array wrapper that automatically extends rows down

    >>> a = AutoExtending(10, 14)
    >>> a.shape
    (10, 14)
    >>> a[1] = 'i'
    >>> a[3:4, :] = 'i' * 14
    >>> a[16:17, :] = 'j' * 14
    >>> a.shape, a[16, 0]
    ((17, 14), 'j')
    """
    def __init__(self, rows, columns):
        self.array = numpy.zeros((rows, columns), dtype=numpy.character)
    def __setitem__(self, where, value):
        if isinstance(where, int):
            if where >= self.array.shape[0]:
                self.array.resize(where + 1, self.array.shape[1])
        elif isinstance(where, tuple) and len(where) == 2:
            if where[0].stop > self.array.shape[0]:
                self.array.resize(where[0].stop, self.array.shape[1])
        else:
            print 'I bet this will raise a slice index error'
        self.array.__setitem__(where, value)
    def __getitem__(self, *args):
        return self.array.__getitem__(*args)
    def __repr__(self):
        return self.array.__repr__()
    def __getattribute__(self, att):
        if att in ['array']:
            return object.__getattribute__(self, att)
        return getattr(self.array, att)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
