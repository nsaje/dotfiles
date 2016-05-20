from django.test import TestCase
from django.template import Context, Template

import backtosql
from backtosql import helpers


class TestSQLMixin(object):

    def assertSQLEquals(self, first, second):
        first = backtosql.clean_sql(first).upper().replace(' ', '').replace('\n', '')
        second = backtosql.clean_sql(second).upper().replace(' ', '').replace('\n', '')
        self.assertEqual(first, second)


class TestRenderMixin(object):

    def assertTemplateRenderEquals(self, template, context, output):
        t = Template('{% load backtosql_tags %}'+template)
        c = Context(context)
        self.assertEqual(t.render(c), output)


class ColumnTestCase(TestCase):

    def test_only_column(self):
        column = backtosql.Column('cat', alias='py_cat')
        self.assertEquals(column.only_column(), 'cat')
        self.assertEquals(column.only_column(prefix='t'), 't.cat')

        self.assertEquals(column.column_as_alias(), 'cat AS py_cat')
        self.assertEquals(column.column_as_alias(prefix='t'), 't.cat AS py_cat')

        self.assertEquals(column.only_alias(), 'py_cat')
        self.assertEquals(column.only_alias(prefix='t'), 't.py_cat')

    def test_g_no_alias(self):
        column = backtosql.Column('cat')
        self.assertEquals(column.only_column(), 'cat')
        self.assertEquals(column.only_column(prefix='t'), 't.cat')

        with self.assertRaises(backtosql.BackToSQLException):
            column.column_as_alias()

        with self.assertRaises(backtosql.BackToSQLException):
            column.only_alias()

    def test_set_group(self):
        column = backtosql.Column('cat', group=1)
        self.assertEquals(column.group, 1)


class TemplateColumnTestCase(TestCase):

    def test_only_column(self):
        column = backtosql.TemplateColumn('test_col.sql', {
            'column_name': 'cat',
            'multiplier': 100,
        }, alias='py_cat')

        self.assertEquals(column.only_column(), "SUM(cat)*100")
        self.assertEquals(column.only_column('t'), "SUM(t.cat)*100")

        self.assertEquals(column.column_as_alias(), "SUM(cat)*100 AS py_cat")
        self.assertEquals(column.column_as_alias('t'), "SUM(t.cat)*100 AS py_cat")

        self.assertEquals(column.only_alias(), "py_cat")
        self.assertEquals(column.only_alias('t'), "t.py_cat")

    def test_g_no_alias(self):
        column = backtosql.TemplateColumn('test_col.sql', {
            'column_name': 'cat',
            'multiplier': 100,
        })

        self.assertEquals(column.only_column(), "SUM(cat)*100")
        self.assertEquals(column.only_column('t'), "SUM(t.cat)*100")

        with self.assertRaises(backtosql.BackToSQLException):
            self.assertEquals(column.column_as_alias(), "SUM(cat)*100 AS py_cat")

        with self.assertRaises(backtosql.BackToSQLException):
            self.assertEquals(column.only_alias(), "py_cat")


class OrderColumnTestCase(TestCase, TestSQLMixin):
    def test_as_order(self):
        column = backtosql.Column('cat', alias='py_cat')
        order = column.as_order('-cat')

        self.assertIsInstance(order, backtosql.OrderColumn)

    def test_get_direction(self):
        self.assertEquals(helpers.get_order('-cat'), 'DESC')
        self.assertEquals(helpers.get_order('cat'), 'ASC')
        self.assertEquals(helpers.get_order('+cat'), 'ASC')

    def test_column_only_column(self):
        column = backtosql.Column('cat', alias='py_cat')

        order = column.as_order('-py_cat')
        self.assertSQLEquals(order.only_column(), 'cat DESC')
        self.assertSQLEquals(order.only_column(prefix='t'), 't.cat DESC')

        self.assertSQLEquals(order.only_alias(), 'py_cat DESC')
        self.assertSQLEquals(order.only_alias(prefix='t'), 't.py_cat DESC')

        with self.assertRaises(backtosql.BackToSQLException):
            order.column_as_alias()

    def test_template_column_only_column(self):
        column = backtosql.TemplateColumn('test_col.sql', {
            'column_name': 'cat',
            'multiplier': 100,
        }, alias='py_cat')

        order = column.as_order('-py_cat')
        self.assertSQLEquals(order.only_column(), 'SUM(cat)*100 DESC')
        self.assertSQLEquals(order.only_column(prefix='t'), 'SUM(t.cat)*100 DESC')

        self.assertSQLEquals(order.only_alias(), 'py_cat DESC')
        self.assertSQLEquals(order.only_alias(prefix='t'), 't.py_cat DESC')

        with self.assertRaises(backtosql.BackToSQLException):
            order.column_as_alias()


class ModelTestCase(TestCase):

    class ModelA(backtosql.Model):
        py_foo = backtosql.Column('foo', group=1)
        py_bar = backtosql.Column('bar', group=2)
        py_cat = backtosql.TemplateColumn('test_col.sql', {'column_name': 'cat'}, group=1)
        py_dog = backtosql.TemplateColumn('test_col.sql', {'column_name': 'dog'}, group=2)

    def test_init_columns_alias(self):
        self.assertEquals(self.ModelA.py_foo.alias, 'py_foo')
        self.assertEquals(self.ModelA.py_bar.alias, 'py_bar')
        self.assertEquals(self.ModelA.py_cat.alias, 'py_cat')
        self.assertEquals(self.ModelA.py_dog.alias, 'py_dog')

    def test_get_columns(self):
        self.assertItemsEqual(self.ModelA.get_columns(),
                              [self.ModelA.py_foo, self.ModelA.py_bar,
                               self.ModelA.py_cat, self.ModelA.py_dog])

    def test_get_column(self):
        self.assertEquals(self.ModelA.get_column('py_foo'), self.ModelA.py_foo)

    def test_select_columns(self):
        self.assertItemsEqual(self.ModelA.select_columns(), self.ModelA.get_columns())

        self.assertItemsEqual(self.ModelA.select_columns(subset=['py_foo', 'py_bar']),
                              [self.ModelA.py_foo, self.ModelA.py_bar])

        self.assertItemsEqual(self.ModelA.select_columns(group=1),
                              [self.ModelA.py_foo, self.ModelA.py_cat])

        self.assertItemsEqual(self.ModelA.select_columns(subset=['py_foo', 'py_bar'], group=1),
                              [self.ModelA.py_foo])


class FiltersTestCase(TestCase, TestRenderMixin):

    def setUp(self):
        c1 = backtosql.Column('cat', alias='py_cat')
        c2 = backtosql.TemplateColumn('test_col.sql', {'column_name': 'dog', 'multiplier': 131}, alias='py_dog')

    def test_only_column(self):
        c1 = backtosql.Column('cat', alias='py_cat')
        c2 = backtosql.TemplateColumn('test_col.sql', {'column_name': 'dog', 'multiplier': 131}, alias='py_dog')

        context = {"cols": [c1, c2]}

        output = u"cat, SUM(dog)*131"
        template = "{{ cols|only_column }}"
        self.assertTemplateRenderEquals(template, context, output)

        output = u"t.cat, SUM(t.dog)*131"
        template = "{{ cols|only_column:'t' }}"
        self.assertTemplateRenderEquals(template, context, output)

        output = u"cat AS py_cat, SUM(dog)*131 AS py_dog"
        template = "{{ cols|column_as_alias }}"
        self.assertTemplateRenderEquals(template, context, output)

        output = u"t.cat AS py_cat, SUM(t.dog)*131 AS py_dog"
        template = "{{ cols|column_as_alias:'t' }}"
        self.assertTemplateRenderEquals(template, context, output)

        output = u"py_cat, py_dog"
        template = "{{ cols|only_alias }}"
        self.assertTemplateRenderEquals(template, context, output)

        output = u"t.py_cat, t.py_dog"
        template = "{{ cols|only_alias:'t' }}"
        self.assertTemplateRenderEquals(template, context, output)

    def test_no_filter(self):
        context = {"cat": "py_cat"}
        output = u"catpy_cat"
        template = "cat{{ cat }}"
        self.assertTemplateRenderEquals(template, context, output)

    def test_lspace(self):
        context = {"cat": "py_cat"}
        output = u"cat py_cat"
        template = "cat{{ cat|lspace }}"
        self.assertTemplateRenderEquals(template, context, output)

    def test_as_kw(self):
        context = {"cat": "py_cat"}
        output = u"cat AS py_cat"
        template = "cat{{ cat|as_kw }}"
        self.assertTemplateRenderEquals(template, context, output)

    def test_indices(self):
        context = {"cat": ["py_cat", "py_dog", "py_foo"]}
        output = u"1, 2, 3"
        template = "{{ cat|indices }}"
        self.assertTemplateRenderEquals(template, context, output)


class QueryConstructionTestCase(TestCase, TestSQLMixin):

    class ModelA(backtosql.Model):
        py_foo = backtosql.Column('foo', group=1)
        py_bar = backtosql.Column('bar', group=1)
        py_cat = backtosql.TemplateColumn('test_col.sql', {'column_name': 'cat', 'multiplier': '100'}, group=2)
        py_dog = backtosql.TemplateColumn('test_col.sql', {'column_name': 'dog', 'multiplier': '10'}, group=2)

    def test_query(self):
        model = self.ModelA
        breakdown = ['py_foo', 'py_bar']
        order = ['-py_cat', 'py_bar']

        context = {
            'breakdown': model.select_columns(subset=breakdown),
            'aggregates': model.select_columns(group=2),
            'table': 'cats_n_dogs',
            'offset': 50,
            'limit': 100,
            'order': model.select_order(order)
        }

        sql = backtosql.generate_sql('test_query.sql', context)
        expected_sql = """
        SELECT a.foo AS py_foo, a.bar AS py_bar, SUM(a.cat)*100 AS py_cat, SUM(a.dog)*10 AS py_dog
        FROM cats_n_dogs a
        WHERE a.date_from >= %(date_from)s AND a.date_to <= %(date_to)s
        GROUP BY foo, bar,
        ORDER BY py_cat DESC, py_bar ASC
        OFFSET %(offset)s
        LIMIT %(limit)s
        """
        self.assertSQLEquals(sql, expected_sql)


class HelpersTestCase(TestCase):

    def test_clean_alias(self):
        self.assertEquals(helpers.clean_alias('+cat'), 'cat')
        self.assertEquals(helpers.clean_alias('-cat'), 'cat')
        self.assertEquals(helpers.clean_alias('cat'), 'cat')

    def test_clean_prefix(self):
        self.assertEquals(helpers.clean_prefix('t'), 't.')
        self.assertEquals(helpers.clean_prefix('t.'), 't.')
