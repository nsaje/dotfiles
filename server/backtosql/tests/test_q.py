import datetime
import backtosql
from django.test import TestCase

from backtosql.tests.test_backtosql import TestSQLMixin


class QTestCase(TestCase):
    class ModelA(backtosql.Model):
        py_foo = backtosql.Column('foo', group=1)
        py_bar = backtosql.Column('bar', group=2)
        py_cat = backtosql.TemplateColumn('test_col.sql', {'column_name': 'cat'}, group=1)
        py_dog = backtosql.TemplateColumn('test_col.sql', {'column_name': 'dog'}, group=2)

    def test_generate_constraints(self):
        constraints_dict = {
            'py_foo__eq': [1, 2, 3],
            'py_bar': datetime.date.today(),
        }

        c = self.ModelA.get_constraints(constraints_dict)
        constraints, params = c.g()
        self.assertEquals(constraints, "(bar=%s AND foo IN %s)")
        self.assertItemsEqual(params, [[1, 2, 3], datetime.date.today()])

        c = self.ModelA.get_constraints(constraints_dict)
        constraints, params = c.g("v")
        self.assertEquals(constraints, "(v.bar=%s AND v.foo IN %s)")
        self.assertItemsEqual(params, [[1, 2, 3], datetime.date.today()])