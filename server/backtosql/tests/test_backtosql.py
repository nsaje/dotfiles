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

        column = backtosql.Column('cat', alias='cat')
        self.assertEquals(column.g(), 'cat')

    def test_g_w_alias(self):
        column = backtosql.Column('cat')
        self.assertEquals(column.g_w_alias(), 'cat')

        column = backtosql.Column('cat', alias='cat')
        self.assertEquals(column.g_w_alias(), 'cat')

    def test_gen_prefix(self):
        column = backtosql.Column('bla')
        self.assertEquals(column.g('t'), 't.bla')

        column = backtosql.Column('bla', alias='asd')
        self.assertEquals(column.g('t'), 't.bla asd')

    def test_set_group(self):
        column = backtosql.Column('bla', group=1)
        self.assertEquals(column.group, 1)


class TemplateColumnTestCase(TestCase):

    def setUp(self):
        self.tpl_name = 'test_col.sql'
        self.column = backtosql.TemplateColumn('test_col.sql', {
            'column_name': 'bla',
            'multiplier': 100,
        }, alias='asd')

    def test_g(self):
        column = backtosql.TemplateColumn('test_col.sql', {
            'column_name': 'bla',
            'multiplier': 100,
        })
        self.assertEquals(column.g(), "SUM(bla)*100")
        self.assertEquals(column.g('t'), "SUM(t.bla)*100")

    def test_gen_alias(self):
        column = backtosql.TemplateColumn('test_col.sql', {
            'column_name': 'bla',
            'multiplier': 100,
        }, alias='asd')
        self.assertEquals(column.g(), "SUM(bla)*100 asd")
        self.assertEquals(column.g('t'), "SUM(t.bla)*100 asd")

    def test_strip_comments(self):
        column = backtosql.TemplateColumn('test_col_comment.sql', {
            'column_name': 'bla',
            'multiplier': 100,
        }, alias='asd')
        self.assertEquals(column.g(), "SUM(bla)*100 asd")
        self.assertEquals(column.g('t'), "SUM(t.bla)*100 asd")


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


def template_test(self, template, context, output):
        t = Template('{% load backtosql_tags %}'+template)
        c = Context(context)
        self.assertEqual(t.render(c), output)


class FiltersTestCase(TestCase):

    def test_g(self):
        c1 = backtosql.Column('aha', alias='py_aha')
        c2 = backtosql.TemplateColumn('test_col.sql', {'column_name': 'aa', 'multiplier': 131}, alias='py_aa')

        context = {"cols": [c1, c2]}
        output = u"aha py_aha/SUM(aa)*131 py_aa"
        template = "{{ cols|g|join:'/' }}"
        template_test(self, template, context, output)

        output = u"t.aha py_aha/SUM(t.aa)*131 py_aa"
        template = "{{ cols|g:'t'|join:'/' }}"
        template_test(self, template, context, output)

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

