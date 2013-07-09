
import numpy


class ReplPainter(object):

    # All paint functions should
    # * return an array of the width they were asked for
    # * return an array not larger than the height they were asked for

    def __init__(self, rows=None, columns=None):
        self.width = columns
        self.height = rows

    def display_linize(self, msg, columns=None):
        if columns == None:
            columns = self.width
        display_lines = ([msg[start:end]
                            for start, end in zip(
                                range(0, len(msg), columns),
                                range(columns, len(msg)+columns, columns))]
                        if msg else [''])
        return display_lines

    def paint_history(self, rows, columns, display_lines):
        lines = []
        for r, line in zip(range(rows), display_lines[-rows:]):
            lines.append((line+' '*1000)[:columns])
        r = numpy.array([list(s) for s in lines]) if lines else numpy.zeros((0,0), dtype=numpy.character)
        assert r.shape[0] <= rows, repr(r.shape)+' '+repr(rows)
        assert r.shape[1] <= columns
        return r

    def paint_current_line(self, rows, columns, current_display_line):
        lines = self.display_linize(current_display_line, columns)
        return numpy.array([(list(line)+[' ']*columns)[:columns] for line in lines])

    def paint_infobox(self, rows, columns, msg):
        if not (rows and columns):
            return numpy.zeros((0,0), dtype=numpy.character)
        else:
            lines = msg.split('\n')
        width = min(columns - 2, max([len(line) for line in lines]))
        output_lines = []
        output_lines.extend(self.display_linize('+'+'-'*width+'+', columns))
        for line in lines:
            output_lines.extend(self.display_linize('|'+line+' '*(width - len(line))+'|', columns))
        output_lines.extend(self.display_linize('+'+'-'*width+'+', columns))
        r = numpy.array([(list(x)+[' ']*(width+2))[:width+2] for x in output_lines][:rows])
        assert len(r.shape) == 2
        return r[:rows-1, :]

if __name__ == '__main__':
    r = ReplPainter()
