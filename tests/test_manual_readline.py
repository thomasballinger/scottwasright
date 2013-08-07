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

    def backward_word(self):
        pass

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
