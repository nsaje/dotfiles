from django.test import SimpleTestCase

from . import camel_case


class CamelCaseTest(SimpleTestCase):
    def test_camel_to_snake(self):
        self.assertEqual("", camel_case.camel_to_snake(""))
        self.assertEqual("oneword", camel_case.camel_to_snake("oneword"))
        self.assertEqual("this_is_my_string", camel_case.camel_to_snake("thisIsMyString"))
        self.assertEqual("this_is_my_string", camel_case.camel_to_snake("thisIsMy_string"))

    def test_snake_to_camel(self):
        self.assertEqual("", camel_case.snake_to_camel(""))
        self.assertEqual("oneword", camel_case.snake_to_camel("oneword"))
        self.assertEqual("thisIsMyString", camel_case.snake_to_camel("this_is_my_string"))
        self.assertEqual("thIsIsMyString", camel_case.snake_to_camel("thIs_is_my_string"))
