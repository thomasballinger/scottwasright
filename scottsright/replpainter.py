
from fmtstr.fmtfuncs import *
from fmtstr.fsarray import fsarray

import logging

#TODO take the boring parts of repl.paint out into here?

# All paint functions should
# * return an array of the width they were asked for
# * return an array not larger than the height they were asked for

def display_linize(msg, columns):
    display_lines = ([msg[start:end]
                        for start, end in zip(
                            range(0, len(msg), columns),
                            range(columns, len(msg)+columns, columns))]
                    if msg else [])
    return display_lines

def paint_history(rows, columns, display_lines):
    lines = []
    for r, line in zip(range(rows), display_lines[-rows:]):
        lines.append((fmtstr(line)+' '*1000)[:columns])
    r = fsarray(lines)
    assert r.shape[0] <= rows, repr(r.shape)+' '+repr(rows)
    assert r.shape[1] <= columns, repr(r.shape)+' '+repr(columns)
    return r

def paint_current_line(rows, columns, current_display_line):
    lines = display_linize(current_display_line, columns)
    return fsarray([(line+' '*columns)[:columns] for line in lines])

def matches_lines(rows, columns, matches, current):
    highlight_color = lambda x: red(on_blue(x))
    if not matches:
        return []
    max_match_width = max(len(m) for m in matches)
    words_wide = max(1, (columns - 1) / (max_match_width + 1))
    matches_lines = [fmtstr(' ').join(m.ljust(max_match_width)
                                        if m != current
                                        else highlight_color(m) + ' '*(max_match_width - len(m))
                                      for m in matches[i:i+words_wide])
                     for i in range(0, len(matches), words_wide)]
    logging.debug('match: %r' % current)
    logging.debug('matches_lines: %r' % matches_lines)
    return matches_lines

def formatted_argspec(argspec):
    return argspec[0] + '(' + ", ".join(argspec[1][0]) + ')'

def paint_infobox(rows, columns, matches, argspec, match, docstring, config):
    """Returns painted completions, argspec, match, docstring etc."""
    if not (rows and columns):
        return fsarray(0, 0)
    lines = ((display_linize(blue(formatted_argspec(argspec)), columns-2) if argspec else []) +
             (display_linize(str(argspec), columns-2) if argspec else []) +
             sum((display_linize(line, columns-2) for line in docstring.split('\n')) if docstring else [], []) +
             (matches_lines(rows, columns, matches, match) if matches else [])
             )

    # add borders
    width = min(columns - 2, max([len(line) for line in lines]))
    output_lines = []
    output_lines.append('+'+'-'*width+'+')
    for line in lines:
        output_lines.append('|'+((line+' '*(width - len(line)))[:width])+'|')
    output_lines.append('+'+'-'*width+'+')
    r = fsarray(output_lines[:rows])
    assert len(r.shape) == 2
    #return r
    return fsarray(r[:rows-1, :])

def paint_statusbar(rows, columns, msg):
    return fsarray([on_green(blue(msg.center(columns)))])

if __name__ == '__main__':
    #paint_history(10, 30, ['asdf', 'adsf', 'aadadfadf']).dumb_display()
    import inspect
    h = paint_infobox(10, 30,
                      matches=['asdf', 'adsf', 'aadadfadf'],
                      argspec=inspect.getargspec(paint_infobox),
                      match='asdf',
                      docstring='Something Interesting',
                      config=None)
    h.dumb_display()
