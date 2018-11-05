from django.conf import settings
from django.test import TestCase

from dcron import commands
from dcron import exceptions


class ExtractManagementCommandNameTestCase(TestCase):
    def test_none(self):
        with self.assertRaises(exceptions.ParameterException):
            commands.extract_management_command_name(None)

    def test_empty(self):
        with self.assertRaises(exceptions.ParameterException):
            commands.extract_management_command_name("")

    def test_single_parameter(self):
        with self.assertRaises(exceptions.ParameterException):
            commands.extract_management_command_name("./manage.py")

    def test_wrong_base_command(self):
        with self.assertRaises(exceptions.ParameterException):
            commands.extract_management_command_name("./manage.py migrate")

    def test_correct_command(self):
        command_name = commands.extract_management_command_name("%s somecommand" % settings.DCRON["base_command"])
        self.assertEqual(command_name, "somecommand")

    def test_correct_command_args(self):
        command_name = commands.extract_management_command_name("%s somecommand 7" % settings.DCRON["base_command"])
        self.assertEqual(command_name, "somecommand")

    def test_correct_command_args_params(self):
        command_name = commands.extract_management_command_name(
            "%s somecommand 7 --test" % settings.DCRON["base_command"]
        )
        self.assertEqual(command_name, "somecommand")
