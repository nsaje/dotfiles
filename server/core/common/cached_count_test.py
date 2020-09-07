from unittest import mock

from django.test import TestCase

from . import cached_count


class MyQuerySet(cached_count.CachedCountMixin):
    def count(self):
        return 1

    def query(self):
        return "myquery"


class MyModel:
    objects = MyQuerySet()


class CachedCountTest(TestCase):
    def test_cached_count(self):
        with mock.patch.object(MyModel.objects, "count", return_value=1):
            MyModel.objects.cached_count()
            MyModel.objects.cached_count()
            MyModel.objects.cached_count()
            MyModel.objects.count.assert_called_once()
