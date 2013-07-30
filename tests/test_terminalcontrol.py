import unittest
from scottsright.events import WindowChangeEvent
from cStringIO import StringIO
from scottsright.terminalcontrol import TerminalController

import pyte

class Translator(object):
    def __init__(self):
        self.out = StringIO()
        self.stream = pyte.DebugStream(self.out)
        self.last_tell = 0
    def write(self, msg):
        self.stream.feed(msg)
    def all_output(self):
        self.out.seek(0)
        return self.out.read()
    @property
    def last(self):
        tell = self.out.tell()
        self.out.seek(self.last_tell)
        self.last_tell = tell
        return self.out.read()

def translate(data):
    t = Translator()
    t.write(data)
    return t.last

class TestTranslator(unittest.TestCase):
    def test_translator(self):
        t = Translator()
        t.write('hey')
        self.assertEqual(t.last, 'DRAW h \nDRAW e \nDRAW y \n')
        t.write('ho')
        self.assertEqual(t.last, 'DRAW h \nDRAW o \n')
        self.assertEqual(translate('\x1b[25d'), 'CURSOR_TO_LINE 25 \n')

class TestTerminalController(unittest.TestCase):
    def setUp(self):
        self.fake_in = StringIO()
        self.fake_out = StringIO()
        self.t = Translator()
        self.tc = TerminalController(self.fake_in, self.t)

    def test_init(self):
        x = TerminalController(self.fake_in, self.fake_out)
        self.assertIsInstance(x, TerminalController)

    def test_cursor_movement(self):
        self.tc.up()
        self.assertEqual(self.t.last, 'CURSOR_UP 1 \n')
        self.tc.up(17)
        self.assertEqual(self.t.last, 'CURSOR_UP 17 \n')
        self.tc.down(17)
        self.assertEqual(self.t.last, 'CURSOR_DOWN 17 \n')
        self.tc.forward(1)
        self.assertEqual(self.t.last, 'CURSOR_FORWARD 1 \n')
        self.tc.fwd()
        self.assertEqual(self.t.last, 'CURSOR_FORWARD 1 \n')
        self.tc.back()
        self.assertEqual(self.t.last, 'CURSOR_BACK 1 \n')

    def test_clear_commands(self):
        self.tc.scroll_down()
        self.assertEqual(self.t.last, 'INDEX  \n')
        self.tc.erase_rest_of_line()
        self.assertEqual(self.t.last, 'ERASE_IN_LINE 0 \n')
        self.tc.erase_line()
        self.assertEqual(self.t.last, 'ERASE_IN_LINE 2 \n')

    def test_query_cursor_position(self):
        self.tc.query_cursor_position()
        self.assertEqual(self.t.last, "DEBUG 6 unhandled: n, state: arguments\n")

    def test_write(self):
        self.tc.write('hello!')
        self.assertEqual(self.t.last, 'DRAW h \nDRAW e \nDRAW l \nDRAW l \nDRAW o \nDRAW ! \n')

class TestTerminalControllerWithScreen(unittest.TestCase):

    def setUp(self):
        self.stream = pyte.ByteStream()
        class FakeOut(object):
            def write(inner_self, data):
                self.stream.feed(data)
        self.screen = pyte.Screen(20, 81)
        self.stream.attach(self.screen)
        self.fake_in = StringIO()
        self.fake_out = FakeOut()
        self.tc = TerminalController(self.fake_in, self.fake_out)

    def test_get_cursor_position(self):
        """Crap test, I hope a better terminal emulator is found"""
        self.fake_in.write('\x1b[4;10R')
        self.fake_in.seek(0)
        self.assertEqual(self.tc.get_cursor_position(), (4, 10))

    def test_set_cursor_position(self):
        self.tc.set_cursor_position((5, 12))
        self.assertEqual(self.screen.cursor.y, 4)
        self.assertEqual(self.screen.cursor.x, 11)

    def test_get_screen_size(self):
        self.fake_in.write('\x1b[4;10R')
        self.fake_in.write('\x1b[20;81R')
        self.fake_in.seek(0)
        rows, columns = self.tc.get_screen_size()
        self.assertEqual((rows, columns), (20, 81))
        self.assertEqual(self.screen.cursor.y, 3)
        self.assertEqual(self.screen.cursor.x, 9)

#TODO: tests for get_event: gnarly identification of escape sequences
#TODO: tests context manager
#TODO: tests for retrying_read

unittest.main()
