from django.core.exceptions import ValidationError
from django.test import TestCase

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


class ValidateDomainNameTest(TestCase):
    def test_valid(self):
        validation_helper.validate_domain_name("example.com")
        validation_helper.validate_domain_name("app.example.com")
        validation_helper.validate_domain_name("APP.EXAMPLE.COM")

    def test_invalid(self):
        with self.assertRaises(ValidationError):
            validation_helper.validate_domain_name("https://example.com")

        with self.assertRaises(ValidationError):
            validation_helper.validate_domain_name("example.com/")

        with self.assertRaises(ValidationError):
            validation_helper.validate_domain_name("example")
