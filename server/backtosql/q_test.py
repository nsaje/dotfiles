import backtosql
import datetime

from django.test import TestCase


class QTestCase(TestCase, backtosql.TestSQLMixin):
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

        c = backtosql.Q(self.ModelA(), **constraints_dict)
        constraints = c.generate()
        self.assertSQLEquals(constraints, "(bar=%s AND foo=ANY(%s))")
        self.assertItemsEqual(c.get_params(), [[1, 2, 3], datetime.date.today()])

        c = backtosql.Q(self.ModelA(), **constraints_dict)
        constraints = c.generate(prefix="v")
        self.assertSQLEquals(constraints, "(v.bar=%s AND v.foo=ANY(%s))")
        self.assertItemsEqual(c.get_params(), [[1, 2, 3], datetime.date.today()])

    def test_generate_constraints_none(self):
        constraints_dict = {
            'py_foo__eq': 1,
        }

        m = self.ModelA()
        c = backtosql.Q(m, **constraints_dict) & backtosql.Q.none(m)
        constraints = c.generate()
        self.assertSQLEquals(constraints, "((foo=%s) AND (1=%s))")
        self.assertItemsEqual(c.get_params(), [1, 2])

        c = backtosql.Q(m, **constraints_dict) & backtosql.Q.none(m)
        constraints = c.generate(prefix="v")
        self.assertSQLEquals(constraints, "((v.foo=%s) AND (1=%s))")
        self.assertItemsEqual(c.get_params(), [1, 2])

    def test_generate_constraints_empty(self):
        constraints_dict = {}

        m = self.ModelA()
        c = backtosql.Q(m, **constraints_dict)
        constraints = c.generate()
        self.assertSQLEquals(constraints, "1=1")
        self.assertItemsEqual(c.get_params(), [])

    def test_generate_nested_constraints(self):
        constraints_dict = {
            'py_foo__eq': [1, 2, 3],
            'py_bar': datetime.date.today(),
        }

        m = self.ModelA()

        q = backtosql.Q(m, **constraints_dict)
        for i in range(10):
            q |= backtosql.Q(m, **constraints_dict)

        constraints = q.generate(prefix="v")
        expected = '''\
        (((((((((((v.bar=%s AND v.foo=ANY(%s)) OR \
        (v.bar=%s AND v.foo=ANY(%s))) OR \
        (v.bar=%s AND v.foo=ANY(%s))) OR \
        (v.bar=%s AND v.foo=ANY(%s))) OR \
        (v.bar=%s AND v.foo=ANY(%s))) OR \
        (v.bar=%s AND v.foo=ANY(%s))) OR \
        (v.bar=%s AND v.foo=ANY(%s))) OR \
        (v.bar=%s AND v.foo=ANY(%s))) OR \
        (v.bar=%s AND v.foo=ANY(%s))) OR \
        (v.bar=%s AND v.foo=ANY(%s))) OR \
        (v.bar=%s AND v.foo=ANY(%s)))\
        '''

        self.assertSQLEquals(constraints, expected.replace('        ', ''))
        self.assertItemsEqual(q.get_params(), [[1, 2, 3], datetime.date.today()] * 11)

    def test_generate_nested_constraints_too_deep(self):
        constraints_dict = {
            'py_foo__eq': [1, 2, 3],
            'py_bar': datetime.date.today(),
        }

        q = backtosql.Q(self.ModelA, **constraints_dict)
        q.MAX_RECURSION_DEPTH = 10

        for i in range(10):
            q |= backtosql.Q(self.ModelA, **constraints_dict)

        with self.assertRaises(backtosql.BackToSQLException):
            q.generate(prefix="v")

    def test_generate_from_a_list(self):
        constraints_dict = {
            'py_foo__eq': [1, 2, 3],
            'py_bar': datetime.date.today(),
        }

        q = backtosql.Q(self.ModelA(), *[backtosql.Q(self.ModelA(), **constraints_dict) for x in range(10)])
        q.join_operator = q.OR

        constraints = q.generate("TROL")
        expected = '''\
        ((TROL.bar=%s AND TROL.foo=ANY(%s)) OR \
        (TROL.bar=%s AND TROL.foo=ANY(%s)) OR \
        (TROL.bar=%s AND TROL.foo=ANY(%s)) OR \
        (TROL.bar=%s AND TROL.foo=ANY(%s)) OR \
        (TROL.bar=%s AND TROL.foo=ANY(%s)) OR \
        (TROL.bar=%s AND TROL.foo=ANY(%s)) OR \
        (TROL.bar=%s AND TROL.foo=ANY(%s)) OR \
        (TROL.bar=%s AND TROL.foo=ANY(%s)) OR \
        (TROL.bar=%s AND TROL.foo=ANY(%s)) OR \
        (TROL.bar=%s AND TROL.foo=ANY(%s)))'''
        self.assertSQLEquals(constraints, expected.replace('        ', ''))
        self.assertItemsEqual(q.get_params(), [[1, 2, 3], datetime.date.today()] * 10)

    def test_generate_tmp_tables(self):
        q = backtosql.Q(self.ModelA(), py_foo=[1, 2, 3], py_bar=[u'a', 'b', 'c'])
        q.use_tmp_tables = True

        constraints = q.generate("TROL")
        create_tmp_tables = q.get_create_tmp_tables()
        drop_tmp_tables = q.get_drop_tmp_tables()

        expected_sql = '''
        (TROL.bar IN (SELECT id FROM tmp_filter_bar_fa43994f0e6a55b39e126bf112a28c13d3280b30) AND
        TROL.foo IN (SELECT id FROM tmp_filter_foo_0017c395f39ceeaee171dff6a1b5bb3d6388e221))'''
        expected_create_sql = '''
        CREATE TEMP TABLE tmp_filter_bar_fa43994f0e6a55b39e126bf112a28c13d3280b30 (id text);
        INSERT INTO tmp_filter_bar_fa43994f0e6a55b39e126bf112a28c13d3280b30 (id) VALUES (%s),(%s),(%s);
        CREATE TEMP TABLE tmp_filter_foo_0017c395f39ceeaee171dff6a1b5bb3d6388e221 (id int);
        INSERT INTO tmp_filter_foo_0017c395f39ceeaee171dff6a1b5bb3d6388e221 (id) VALUES (%s),(%s),(%s);'''
        expected_drop_sql = '''
        DROP TABLE tmp_filter_bar_fa43994f0e6a55b39e126bf112a28c13d3280b30;
        DROP TABLE tmp_filter_foo_0017c395f39ceeaee171dff6a1b5bb3d6388e221;'''

        self.assertSQLEquals(constraints, expected_sql)
        self.assertEqual(q.get_params(), [])
        self.assertSQLEquals(create_tmp_tables[0], expected_create_sql)
        self.assertEqual(create_tmp_tables[1], ['a', 'b', 'c', 1, 2, 3])
        self.assertSQLEquals(drop_tmp_tables[0], expected_drop_sql)
        self.assertEqual(drop_tmp_tables[1], [])

    def test_generate_tmp_tables_none(self):
        q = backtosql.Q(self.ModelA(), py_foo=1, py_bar='a')
        q.use_tmp_tables = True

        q.generate("TROL")
        create_tmp_tables = q.get_create_tmp_tables()
        drop_tmp_tables = q.get_drop_tmp_tables()

        self.assertIsNone(create_tmp_tables)
        self.assertIsNone(drop_tmp_tables)
