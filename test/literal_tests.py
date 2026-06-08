import unittest

from talk import Talk

class LiteralTests(unittest.TestCase):
    def test_write_simple_value(self):
        result = Talk("The value of a is 3.")
        self.assertEqual('3', result.A)

    def test_write_string_literal(self):
        result = Talk("The value of a is \'foo\'")
        self.assertEqual('foo', result.A)

    def test_write_string_literal_double_quotes(self):
        result = Talk("The value of a is \"foo\"")
        self.assertEqual('foo\n', str(result))

    def test_query_simple_value(self):
        result = Talk("The value of a is 3. What is the value of a?")
        self.assertEqual('3\n', str(result))

    def test_query_echo_string_literal(self):
        result = Talk("What is the value of \'foo\'?")
        self.assertEqual("foo\n", str(result))

    def test_basic_math(self):
        result = Talk("What is 2 + 2?")
        self.assertEqual('4\n', str(result))

    def test_basic_math_with_variables(self):
        result = Talk("The value of a is 2. What is a + a?")
        self.assertEqual('4\n', str(result))

    def test_basic_math_with_variables_and_literals(self):
        result = Talk("The value of a is 2. What is a + 3?")
        self.assertEqual('5\n', str(result))

    def test_basic_math_with_variables_and_string_literals(self):
        result = Talk("The value of a is 2. What is a + \'3\'?")
        self.assertEqual('5\n', str(result))

    def test_basic_math_with_multiple_variables(self):
        result = Talk("The value of a is 2. The value of b is 3. What is a + b?")
        self.assertEqual('5\n', str(result))
    