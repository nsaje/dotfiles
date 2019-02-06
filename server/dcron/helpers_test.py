from django.test import TestCase

from dcron import helpers


class ParseArgumentsTestCase(TestCase):
    def test_no_args(self):
        with self.assertRaises(ValueError):
            helpers.get_command_and_arguments([])

    def test_single_arg(self):
        with self.assertRaises(ValueError):
            helpers.get_command_and_arguments(["arg"])

    def test_wrong_args(self):
        with self.assertRaises(ValueError):
            helpers.get_command_and_arguments(["arg0", "arg1"])

    def test_minimum_args(self):
        command, arguments = helpers.get_command_and_arguments(["./manage.py", "management_command"])
        self.assertEqual(command, "management_command")
        self.assertEqual(arguments, [])

    def test_additional_args(self):
        command, arguments = helpers.get_command_and_arguments(
            ["./manage.py", "management_command", "--input", "some_file"]
        )
        self.assertEqual(command, "management_command")
        self.assertEqual(arguments, ["--input", "some_file"])

    def test_dcron_minimum_args(self):
        command, arguments = helpers.get_command_and_arguments(["./manage.py", "dcron_launcher", "management_command"])
        self.assertEqual(command, "management_command")
        self.assertEqual(arguments, [])

    def test_dcron_additional_args(self):
        command, arguments = helpers.get_command_and_arguments(
            ["./manage.py", "dcron_launcher", "management_command", "--input", "some_file"]
        )
        self.assertEqual(command, "management_command")
        self.assertEqual(arguments, ["--input", "some_file"])
