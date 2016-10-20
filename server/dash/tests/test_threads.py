from django.test import TestCase
from dash import threads


class SomeException(Exception):
    pass


class AsyncFunctionTest(TestCase):
    def test_asycfunction(self):

        def fn():
            return range(5)

        afn = threads.AsyncFunction(fn)
        afn.start()

        afn.join()
        self.assertEqual(afn.get_result(), range(5))

    def test_asycfunction_exception(self):
        def fn():
            raise SomeException()

        afn = threads.AsyncFunction(fn)
        afn.start()

        afn.join()

        with self.assertRaises(SomeException):
            afn.get_result()
