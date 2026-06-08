import unittest

from talk import DECLARATIVE, Talk


class FunctionTests(unittest.TestCase):
    def test_fibonacci_example(self):
        text = (
            "A dummy uses numbers. A dummy can calculate. A dummy requires a number to calculate. "
            "When the dummy calculates, if the number equals 1, then the result is 0. "
            "When the dummy calculates, if the number equals 2, then the result is 1. "
            "When the dummy calculates, if the number is greater than 2, then the result is the sum of calculating (the number minus 1, and calculating (the number minus 2). "
            "The dummy calculates with 8. What is the result?"
        )
        result = Talk(text)
        self.assertEqual('13\n', str(result))

    def test_sentence_categorization_for_action_sentences(self):
        talk = Talk('')
        self.assertEqual('action_definition', talk.categorize_sentence('A dummy can calculate.', DECLARATIVE))
        self.assertEqual('action_definition', talk.categorize_sentence('A dummy requires a number to calculate.', DECLARATIVE))
        self.assertEqual('when', talk.categorize_sentence('When the dummy calculates, if the number equals 1, then the result is 0.', DECLARATIVE))

    def test_action_definition_and_parameter_storage(self):
        result = Talk('A dummy can calculate. A dummy requires a number to calculate.')
        self.assertIn(('dummy', 'calculate'), result.actions)
        self.assertEqual(['number'], result.actions[('dummy', 'calculate')].parameters)

    def test_when_rule_is_stored_on_action_definition(self):
        result = Talk('A dummy can calculate. A dummy requires a number to calculate. When the dummy calculates, if the number equals 1, then the result is 0.')
        rules = result.actions[('dummy', 'calculate')].rules
        self.assertEqual(1, len(rules))
        self.assertEqual('result', rules[0].target)
        self.assertEqual('0', rules[0].expression)
        self.assertTrue(rules[0].condition({'number': 1}))
