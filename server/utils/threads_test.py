from django.test import TestCase
from utils import threads


class SomeException(Exception):
    pass


class AsyncFunctionTest(TestCase):
    def test_asycfunction(self):
        def fn():
            return list(range(5))

        afn = threads.AsyncFunction(fn)
        afn.start()

        afn.join()
        self.assertEqual(afn.get_result(), list(range(5)))

    def test_asycfunction_exception(self):
        def fn():
            raise SomeException()

        afn = threads.AsyncFunction(fn)
        afn.start()

        afn.join()

        with self.assertRaises(SomeException):
            afn.get_result()
