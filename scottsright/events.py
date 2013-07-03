"""Language for describing events that in terminal"""
class WindowChangeEvent(object):
    def __init__(self, rows, columns):
        self.rows = rows
        self.columns = columns
    x = width = property(lambda self: self.columns)
    y = height = property(lambda self: self.rows)
