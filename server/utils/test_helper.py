import datetime
import http.client
import itertools
import operator
from contextlib import contextmanager
from functools import reduce
from typing import Iterable

import django.core.files
import mock
from django.contrib.auth.models import Permission
from django.test.client import RequestFactory
from parameterized import param  # type: ignore

import core.models
import zemauth.features.entity_permission


def add_permissions(user, permissions):
    """ utility intended to be used in unit tests only """
    for permission in permissions:
        user.user_permissions.add(Permission.objects.get(codename=permission))


def remove_permissions(user, permissions):
    """ utility intended to be used in unit tests only """
    for permission in permissions:
        user.user_permissions.remove(Permission.objects.get(codename=permission))


def add_entity_permissions(user, permissions, entity):
    """ utility intended to be used in unit tests only """
    for permission in permissions:
        if entity is None:
            entity_permission = zemauth.features.entity_permission.EntityPermission(user=user, permission=permission)
            entity_permission.save()
        elif isinstance(entity, core.models.Agency):
            entity_permission = zemauth.features.entity_permission.EntityPermission(
                user=user, permission=permission, agency=entity
            )
            entity_permission.save()
        elif isinstance(entity, core.models.Account):
            entity_permission = zemauth.features.entity_permission.EntityPermission(
                user=user, permission=permission, account=entity
            )
            entity_permission.save()


def remove_entity_permissions(user, permissions, entity):
    """ utility intended to be used in unit tests only """
    for permission in permissions:
        if isinstance(entity, core.models.Agency):
            user.entitypermission_set.filter(permission=permission, agency=entity).delete()
        elif isinstance(entity, core.models.Account):
            user.entitypermission_set.filter(permission=permission, account=entity).delete()


def fake_request(user, url=""):
    rf = RequestFactory()
    r = rf.get(url)
    r.user = user
    return r


def mock_file(name, content):
    m = mock.Mock(spec=django.core.files.File)
    m.read.return_value = content
    m.name = name
    return m


class MockDateTime(datetime.datetime):
    def __new__(cls, *args, **kwargs):
        return datetime.datetime.__new__(cls, *args, **kwargs)


class AlmostMatcher:
    def __init__(self, obj, ndigits=4):
        self.obj = obj
        self.ndigits = ndigits

    def __eq__(self, other):
        return round(self.obj, self.ndigits) == round(other, self.ndigits)

    def __repr__(self):
        return repr(self.obj)


class QuerySetMatcher:
    def __init__(self, obj):
        self.obj = obj

    def __eq__(self, other):
        a = sorted(list(self.obj), key=lambda x: x.pk)
        b = sorted(list(other), key=lambda x: x.pk)
        return a == b

    def __repr__(self):
        return "<QuerySet %s>" % list(self.obj)


class ListMatcher:
    """Checks if both lists (or list like objects) contain the same elements.
    For use with Mock.assert_called_with()."""

    def __init__(self, obj, key=None):
        self.obj = obj
        self.key = key

    def __eq__(self, other):
        return sorted(self.obj, key=self.key) == sorted(other, key=self.key)

    def __iter__(self):
        for i in self.obj:
            yield i

    def __repr__(self):
        return f"{type(self).__name__}({repr(self.obj)})"


class TypeMatcher:
    def __init__(self, expected_type):
        self.expected_type = expected_type

    def __eq__(self, other):
        return isinstance(other, self.expected_type)


class SubstringMatcher:
    expected_substring: str

    def __init__(self, expected_substring: str):
        self.expected_substring = expected_substring

    def __eq__(self, other):
        return self.expected_substring in other

    def __repr__(self):
        return f'<{type(self).__name__} "...{self.expected_substring}...">'


def is_equal(val1, val2):
    if isinstance(val1, float) or isinstance(val2, float):
        return round(val1, 4) == round(val2, 4)
    else:
        return val1 == val2


def dicts_match_for_keys(dct1, dct2, keys):
    if not reduce(operator.iand, (k in dct1 and k in dct2 for k in keys), True):
        return False
    return reduce(operator.iand, (is_equal(dct1[k], dct2[k]) for k in keys), True)


def sequence_of_dicts_match_for_keys(dicts1, dicts2, keys):
    if len(dicts1) != len(dicts2):
        return False
    return reduce(operator.iand, (dicts_match_for_keys(dct1, dct2, keys) for dct1, dct2 in zip(dicts1, dicts2)), True)


def prepare_mock_urlopen(mock_urlopen, exception=None):
    if exception:
        mock_urlopen.side_effect = exception
        return

    mock_request = mock.Mock()
    mock_request.status_code = http.client.OK
    mock_urlopen.return_value = mock_request


def format_csv_content(content):
    # Expected content - All fields are double-quoted and
    lines_formatted = []
    for line in content.split("\r\n"):
        if not line:
            continue
        fields = line.split(",")
        fields_formatted = ['"' + f + '"' for f in fields]
        line_formatted = ",".join(fields_formatted)
        lines_formatted.append(line_formatted)

    formatted_content = "\r\n".join(lines_formatted) + "\r\n"
    return formatted_content


@contextmanager
def disable_auto_now_add(cls, field_name):
    field = cls._meta.get_field(field_name)
    prev_auto_now_add = field.auto_now_add
    field.auto_now_add = False
    yield
    field.auto_now_add = prev_auto_now_add


@contextmanager
def disable_auto_now(cls, field_name):
    field = cls._meta.get_field(field_name)
    prev_auto_now = field.auto_now
    field.auto_now = False
    yield
    field.auto_now = prev_auto_now


def params_cross_product(*params_iterables: Iterable[param]) -> Iterable[param]:
    """ Returns a cross product of iterables of params for use in parameterized tests.

        The first argument is expected to be the test case name.

        For example:

        >>> l1 = [param("foo", 1, a=1), param("bar", 2, a=2)]
        >>> l2 = [param("baz", b=1)]
        >>> list(params_cross_product(l1, l2))
        [param(*('foo_baz', 1), **{'a': 1, 'b': 1}), param(*('bar_baz', 2), **{'a': 2, 'b': 1})]
    """

    def _params_reducer(p1, p2):
        name = p1.args[0] + "_" + p2.args[0]
        args = (name,) + p1.args[1:] + p2.args[1:]
        kwargs = {**p1.kwargs, **p2.kwargs}
        return param(*args, **kwargs)

    return (reduce(_params_reducer, product) for product in itertools.product(*params_iterables))
