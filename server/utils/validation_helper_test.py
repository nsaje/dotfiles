from django.test import TestCase

from django.core.exceptions import ValidationError

from . import validation_helper


class ValidatePlainTextTest(TestCase):
    def test_valid(self):
        validation_helper.validate_plain_text("test text")
        validation_helper.validate_plain_text("Is 3 > 2?")
        validation_helper.validate_plain_text("I <3 this")

    def test_invalid(self):
        with self.assertRaises(ValidationError):
            validation_helper.validate_plain_text("Some <b>test</b> text")

        with self.assertRaises(ValidationError):
            validation_helper.validate_plain_text('<a href="https://test.com">asdf')
