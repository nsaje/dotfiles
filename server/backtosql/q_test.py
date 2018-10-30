import datetime

from django.test import TestCase

import backtosql


class QTestCase(TestCase, backtosql.TestSQLMixin):
    class ModelA(backtosql.Model):
        py_foo = backtosql.Column("foo", group=1)
        py_bar = backtosql.Column("bar", group=2)
        py_cat = backtosql.TemplateColumn("test_col.sql", {"column_name": "cat"}, group=1)
        py_dog = backtosql.TemplateColumn("test_col.sql", {"column_name": "dog"}, group=2)

    def test_generate_constraints(self):
        constraints_dict = {"py_foo__eq": [1, 2, 3], "py_bar": datetime.date.today()}

        c = backtosql.Q(self.ModelA(), **constraints_dict)
        constraints = c.generate()
        self.assertSQLEquals(constraints, "(bar=%s AND foo=ANY(%s))")
        self.assertCountEqual(c.get_params(), [[1, 2, 3], datetime.date.today()])

        c = backtosql.Q(self.ModelA(), **constraints_dict)
        constraints = c.generate(prefix="v")
        self.assertSQLEquals(constraints, "(v.bar=%s AND v.foo=ANY(%s))")
        self.assertCountEqual(c.get_params(), [[1, 2, 3], datetime.date.today()])

    def test_generate_constraints_none(self):
        constraints_dict = {"py_foo__eq": 1}

        m = self.ModelA()
        c = backtosql.Q(m, **constraints_dict) & backtosql.Q.none(m)
        constraints = c.generate()
        self.assertSQLEquals(constraints, "((foo=%s) AND (1=%s))")
        self.assertCountEqual(c.get_params(), [1, 2])

        c = backtosql.Q(m, **constraints_dict) & backtosql.Q.none(m)
        constraints = c.generate(prefix="v")
        self.assertSQLEquals(constraints, "((v.foo=%s) AND (1=%s))")
        self.assertCountEqual(c.get_params(), [1, 2])

    def test_generate_constraints_empty(self):
        constraints_dict = {}

        m = self.ModelA()
        c = backtosql.Q(m, **constraints_dict)
        constraints = c.generate()
        self.assertSQLEquals(constraints, "1=1")
        self.assertCountEqual(c.get_params(), [])

    def test_generate_nested_constraints(self):
        constraints_dict = {"py_foo__eq": [1, 2, 3], "py_bar": datetime.date.today()}

        m = self.ModelA()

        q = backtosql.Q(m, **constraints_dict)
        for i in range(10):
            q |= backtosql.Q(m, **constraints_dict)

        constraints = q.generate(prefix="v")
        expected = """\
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
        """

        self.assertSQLEquals(constraints, expected.replace("        ", ""))
        self.assertCountEqual(q.get_params(), [[1, 2, 3], datetime.date.today()] * 11)

    def test_generate_nested_constraints_too_deep(self):
        constraints_dict = {"py_foo__eq": [1, 2, 3], "py_bar": datetime.date.today()}

        q = backtosql.Q(self.ModelA, **constraints_dict)
        q.MAX_RECURSION_DEPTH = 10

        for i in range(10):
            q |= backtosql.Q(self.ModelA, **constraints_dict)

        with self.assertRaises(backtosql.BackToSQLException):
            q.generate(prefix="v")

    def test_generate_from_a_list(self):
        constraints_dict = {"py_foo__eq": [1, 2, 3], "py_bar": datetime.date.today()}

        q = backtosql.Q(self.ModelA(), *[backtosql.Q(self.ModelA(), **constraints_dict) for x in range(10)])
        q.join_operator = q.OR

        constraints = q.generate("TROL")
        expected = """\
        ((TROL.bar=%s AND TROL.foo=ANY(%s)) OR \
        (TROL.bar=%s AND TROL.foo=ANY(%s)) OR \
        (TROL.bar=%s AND TROL.foo=ANY(%s)) OR \
        (TROL.bar=%s AND TROL.foo=ANY(%s)) OR \
        (TROL.bar=%s AND TROL.foo=ANY(%s)) OR \
        (TROL.bar=%s AND TROL.foo=ANY(%s)) OR \
        (TROL.bar=%s AND TROL.foo=ANY(%s)) OR \
        (TROL.bar=%s AND TROL.foo=ANY(%s)) OR \
        (TROL.bar=%s AND TROL.foo=ANY(%s)) OR \
        (TROL.bar=%s AND TROL.foo=ANY(%s)))"""
        self.assertSQLEquals(constraints, expected.replace("        ", ""))
        self.assertCountEqual(q.get_params(), [[1, 2, 3], datetime.date.today()] * 10)
