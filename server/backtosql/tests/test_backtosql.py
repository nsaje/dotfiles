import datetime

from django.test import TestCase
from django.template import Context, Template

import backtosql
import backtosql.helpers
from backtosql.templatetags import backtosql_tags


class ColumnTestCase(TestCase):
    def test_g(self):
        column = backtosql.Column('cat')
        self.assertEquals(column.g(), 'cat')
        self.assertEquals(column.g(prefix='t'), 't.cat')

        column = backtosql.Column('cat', alias='py_cat')
        self.assertEquals(column.g(), 'cat')
        self.assertEquals(column.g(prefix='t'), 't.cat')

    def test_g_w_alias(self):
        column = backtosql.Column('cat')
        self.assertEquals(column.g_w_alias(), 'cat')
        self.assertEquals(column.g_w_alias(prefix='t'), 't.cat')

        column = backtosql.Column('cat', alias='py_cat')
        self.assertEquals(column.g_w_alias(), 'cat AS py_cat')
        self.assertEquals(column.g_w_alias(prefix='t'), 't.cat AS py_cat')

    def test_g_alias(self):
        column = backtosql.Column('cat')
        with self.assertRaises(backtosql.BackToSQLException):
            column.g_alias('t')

        column = backtosql.Column('cat', alias='py_cat')
        self.assertEquals(column.g_alias('t'), 't.py_cat')

    def test_set_group(self):
        column = backtosql.Column('cat', group=1)
        self.assertEquals(column.group, 1)


class TemplateColumnTestCase(TestCase):

    def setUp(self):
        self.tpl_name = 'test_col.sql'
        self.column = backtosql.TemplateColumn('test_col.sql', {
            'column_name': 'cat',
            'multiplier': 100,
        }, alias='py_cat')

    def test_g(self):
        column = backtosql.TemplateColumn('test_col.sql', {
            'column_name': 'cat',
            'multiplier': 100,
        })
        self.assertEquals(column.g(), "SUM(cat)*100")
        self.assertEquals(column.g('t'), "SUM(t.cat)*100")

    def test_g_w_alias(self):
        column = backtosql.TemplateColumn('test_col.sql', {
            'column_name': 'cat',
            'multiplier': 100,
        }, alias='py_cat')
        self.assertEquals(column.g(), "SUM(cat)*100 AS py_cat")
        self.assertEquals(column.g('t'), "SUM(t.cat)*100 AS py_cat")

    def test_strip_comments(self):
        column = backtosql.TemplateColumn('test_col_comment.sql', {
            'column_name': 'cat',
            'multiplier': 100,
        }, alias='py_cat')
        self.assertEquals(column.g(), "SUM(cat)*100 AS py_cat")
        self.assertEquals(column.g('t'), "SUM(t.cat)*100 AS py_cat")


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

    def test_select_columns(self):
        self.assertItemsEqual(self.ModelA.select_columns(), self.ModelA.get_columns())

        self.assertItemsEqual(self.ModelA.select_columns(subset=['py_foo', 'py_bar']),
                              [self.ModelA.py_foo, self.ModelA.py_bar])

        self.assertItemsEqual(self.ModelA.select_columns(group=1),
                              [self.ModelA.py_foo, self.ModelA.py_cat])

        self.assertItemsEqual(self.ModelA.select_columns(subset=['py_foo', 'py_bar'], group=1),
                              [self.ModelA.py_foo])


class FiltersTestCase(TestCase):

    def setUp(self):
        c1 = backtosql.Column('cat', alias='py_cat')
        c2 = backtosql.TemplateColumn('test_col.sql', {'column_name': 'dog', 'multiplier': 131}, alias='py_dog')

    def assertTemplateRenderEquals(self, template, context, output):
        t = Template('{% load backtosql_tags %}'+template)
        c = Context(context)
        self.assertEqual(t.render(c), output)

    def test_g_w_alias(self):
        c1 = backtosql.Column('cat', alias='py_cat')
        c2 = backtosql.TemplateColumn('test_col.sql', {'column_name': 'dog', 'multiplier': 131}, alias='py_dog')

        context = {"cols": [c1, c2]}
        output = u"cat AS py_aha, SUM(dog)*131 py_dog"
        template = "{{ cols|g_w_alias|join:',' }}"
        self.assertTemplateRenderEquals(template, context, output)

        output = u"t.cat AS py_cat, SUM(t.dog)*131 AS py_dog"
        template = "{{ cols|g_w_alias:'t'|join:',' }}"
        self.assertTemplateRenderEquals(template, context, output)

    def test_lspace(self):
        context = {"a": "asd"}
        output = u"bbb asd"
        template = "bbb{{ a|lspace }}"
        template_test(self, template, context, output)

        context = {"a": "asd"}
        output = u"bbbasd"
        template = "bbb{{ a }}"
        template_test(self, template, context, output)


class QueryConstructionTestCase(TestCase):
    class ModelA(backtosql.Model):
        py_foo = backtosql.Column('foo', group=1)
        py_bar = backtosql.Column('bar', group=1)
        py_cat = backtosql.TemplateColumn('test_col.sql', {'column_name': 'cat', 'multiplier':'100'}, group=2)
        py_dog = backtosql.TemplateColumn('test_col.sql', {'column_name': 'dog', 'multiplier':'10'}, group=2)

    def test_query(self):
        model = self.ModelA
        breakdown = ['py_foo', 'py_bar']
        partition = ['py_foo']
        order = ['-py_cat', 'py_bar']

        context = {
            'columns': model.get_columns(),
            'breakdown': model.select_columns(subset=breakdown),
            'partition': model.select_columns(subset=partition),
            'order': [backtosql.OrderWrapper(model.get_column(c), c) for c in order],
        }

        sql = backtosql.generate_sql('test_query.sql', context)
        backtosql.helpers.printsql(sql)
        self.assertTrue(False)

