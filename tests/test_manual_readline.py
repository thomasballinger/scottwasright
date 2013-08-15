from scottsright.manual_readline import *
import unittest

class TestManualReadline(unittest.TestCase):
    def setUp(self):
        self._line = "this is my test string"

    def tearDown(self):
        pass

    def test_left_arrow_at_zero(self):
        pos = 0
        expected = (pos, self._line)
        result = left_arrow(pos, self._line)
        self.assertEquals(expected, result)

    def test_left_arrow_at_non_zero(self):
        for i in xrange(1, len(self._line)):
            expected = (i-1, self._line)
            result = left_arrow(i, self._line)
            self.assertEqual(expected, result)

    def test_right_arrow_at_end(self):
        pos = len(self._line)
        expected = (pos, self._line)
        result = right_arrow(pos, self._line)
        self.assertEquals(expected, result)

    def test_right_arrow_at_non_end(self):
        for i in xrange(len(self._line) - 1):
            expected = (i + 1, self._line)
            result = right_arrow(i, self._line)
            self.assertEquals(expected, result)

    def test_beginning_of_line(self):
        expected = (0, self._line)
        for i in xrange(len(self._line)):
            result = beginning_of_line(i, self._line)
            self.assertEquals(expected, result)

    def test_end_of_line(self):
        expected = (len(self._line), self._line)
        for i in xrange(len(self._line)):
            result = end_of_line(i, self._line)
            self.assertEquals(expected, result)

    def test_forward_word(self):
        line = "going from here to_here"
        start_pos = 11
        next_word_pos = 16
        self.assertEquals(line[start_pos], 'h')
        self.assertEquals(line[next_word_pos], 't')
        expected = (next_word_pos, line)
        result = forward_word(start_pos, line)
        self.assertEquals(expected, result)

    def test_forward_word_tabs(self):
        line = "going from here      to_here"
        start_pos = 11
        next_word_pos = 21
        self.assertEquals(line[start_pos], 'h')
        self.assertEquals(line[next_word_pos], 't')
        expected = (next_word_pos, line)
        result = forward_word(start_pos, line)
        self.assertEquals(expected, result)

    def test_back_word(self):
        line = "going to here from_here"
        start_pos = 14
        prev_word_pos = 9
        self.assertEquals(line[start_pos], 'f')
        self.assertEquals(line[prev_word_pos], 'h')
        expected = (prev_word_pos, line)
        result = back_word(start_pos, line)
        self.assertEquals(expected, result)

    def test_last_word_pos(self):
        line = "a word"
        expected = 2
        result = last_word_pos(line)
        self.assertEquals(expected, result)

    def test_last_word_pos_single_word(self):
        line = "word"
        expected = 0
        result = last_word_pos(line)
        self.assertEquals(expected, result)

    def test_delete(self):
        line = "deletion line"
        pos = 3
        expected = (3, "deltion line")
        result = delete(pos, line)
        self.assertEquals(expected, result)

    def test_delete_from_cursor_back(self):
        line = "everything before this will be deleted"
        expected = (0, "this will be deleted")
        result = delete_from_cursor_back(line.find("this"), line)
        self.assertEquals(expected, result)

    def test_delete_from_cursor_forward(self):
        line = "everything after this will be deleted"
        pos = line.find("this")
        expected = (pos, "everything after ")
        result = delete_from_cursor_forward(line.find("this"), line)
        self.assertEquals(expected, result)

    def test_delete_rest_of_word(self):
        pass

    def test_delete_word_to_cursor(self):
        pass

    def test_yank_prev_killed_text(self):
        pass

    def test_yank_prev_prev_killed_text(self):
        pass

    def test_transpose_character_before_cursor(self):
        pass

    def test_transpose_word_before_cursor(self):
        pass

if __name__ == '__main__':
    unittest.main()
