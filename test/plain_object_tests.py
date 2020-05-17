import unittest

from talk import Talk


class BasicObjectTests(unittest.TestCase):
    def test_object_creation(self):
        """
        Test that defining something as a Person creates the Person class
        :return:
        """
        result = Talk("Ben is a person.")
        self.assertIn('person', result.classes)

    def test_subject_creation(self):
        """
        Test that defining an object as a Person defines that object as a Person.
        :return:
        """
        result = Talk("Ben is a person.")
        self.assertEqual(result.classes['person'], type(result.Ben))

    def test_subject_field_no_value_creation(self):
        result = Talk("Ben has a job.")
        self.assertIn('job', vars(result.Ben))

    def test_subject_field_value_creation(self):
        result = Talk("Ben is a person. Ben has a height of 6ft.")
        self.assertEqual("6ft", result.Ben.height)

    def test_subject_field_creation_without_subject_creation(self):
        result = Talk("Ben has a height of 6ft.")
        self.assertEqual("6ft", result.Ben.height)

    def test_subject_field_creation_possessive(self):
        result = Talk("Ben's height is 6ft.")
        self.assertEqual("6ft", result.Ben.height)

    def test_subject_field_access(self):
        result = Talk("Ben is a person. Ben has a height of 6ft. What is the height of Ben?", True)
        self.assertEqual("6ft\n", str(result))

    def test_subject_field_access_possessive(self):
        result = Talk("Ben has a height of 6ft. What is Ben's height?")
        self.assertEqual("6ft\n", str(result))

    def field_first_write(self):
        result = Talk("The height of Ben is 6ft. What is Ben's height?")
        self.assertEqual("6ft\n", str(result))

    @unittest.skip("unsupported alt syntax")
    def test_how_query(self):
        result = Talk("Ben is 6ft tall. How tall is Ben?")
        self.assertEqual("6ft\n", str(result))

    def test_does_query_for_existing_field(self):
        result = Talk("Ben has a job. Does Ben have a job?")
        self.assertEqual("yes\n", str(result))
    
    def test_does_query_for_nonexistant_field(self):
        result = Talk("Ben is a person. Does Ben have a job?")
        self.assertEqual("no\n", str(result))

    def test_does_not_have(self):
        result = Talk("Ben does not have a job.")
        self.assertEqual(False, result.Ben.Job)

    def test_does_query_explicit_negative(self):
        result = Talk("Ben does not have a job. Does Ben have a job?")
        self.assertEqual("no\n", str(result))

    def test_sub_object_access(self):
        result = Talk("My name is Ben.")
        self.assertEqual("Ben", result.My.Name)

    def test_sub_object_query(self):
        result = Talk("My name is Ben. What is my name?")
        self.assertEqual("Ben\n", str(result))
