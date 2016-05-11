import json
import django.test


def drepr(x, sort = True, indent = 4):
    if isinstance(x, dict):
        r = '{\n'
        for (key, value) in (sorted(x.items()) if sort else x.iteritems()):
            r += (' ' * (indent + 4)) + repr(key) + ': '
            r += drepr(value, sort, indent + 4) + ',\n'
        r = r.rstrip(',\n') + '\n'
        r += (' ' * indent) + '}'
    elif hasattr(x, '__iter__'):
        r = '[\n'
        for value in (sorted(x) if sort else x):
            r += (' ' * (indent + 4)) + drepr(value, sort, indent + 4) + ',\n'
        r = r.rstrip(',\n') + '\n'
        r += (' ' * indent) + ']'
    else:
        r = repr(x)
    return r

class TestCase(django.test.TestCase):
    def assertDictEqual(self, d1, d2, msg=None):
        try:
            super(TestCase, self).assertDictEqual(d1, d2, msg)
        except Exception as e:
            print drepr(d1)
            print drepr(d2)
            raise e
