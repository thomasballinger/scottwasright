
from fmtstr.fmtstr import *
from fmtstr.fsarray import fsarray


#TODO take the boring parts of repl.paint out into here?

# All paint functions should
# * return an array of the width they were asked for
# * return an array not larger than the height they were asked for

def display_linize(msg, columns):
    display_lines = ([msg[start:end]
                        for start, end in zip(
                            range(0, len(msg), columns),
                            range(columns, len(msg)+columns, columns))]
                    if msg else [''])
    return display_lines

def paint_history(rows, columns, display_lines):
    lines = []
    for r, line in zip(range(rows), display_lines[-rows:]):
        lines.append((line+' '*1000)[:columns])
    r = fsarray(lines)
    assert r.shape[0] <= rows, repr(r.shape)+' '+repr(rows)
    assert r.shape[1] <= columns
    return r

def paint_current_line(rows, columns, current_display_line):
    lines = display_linize(current_display_line, columns)
    return fsarray([(line+' '*columns)[:columns] for line in lines])

def paint_infobox(rows, columns, msg):
    if not (rows and columns):
        return fsarray(0, 0)
    else:
        lines = msg.split('\n')
    width = min(columns - 2, max([len(line) for line in lines]))
    output_lines = []
    output_lines.extend(display_linize('+'+'-'*width+'+', columns))
    for line in lines:
        output_lines.extend(display_linize('|'+line+' '*(width - len(line))+'|', columns))
    output_lines.extend(display_linize('+'+'-'*width+'+', columns))
    r = fsarray([(x+' '*(width+2))[:width+2] for x in output_lines[:rows]])
    assert len(r.shape) == 2
    return fsarray(r[:rows-1, :])

if __name__ == '__main__':
    #paint_history(10, 30, ['asdf', 'adsf', 'aadadfadf']).dumb_display()
    h = paint_infobox(10, 30, '\n'.join(['asdf', 'adsf', 'aadadfadf']))
    h.dumb_display()
