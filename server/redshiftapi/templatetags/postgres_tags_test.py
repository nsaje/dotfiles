import django.template

from utils.base_test_case import BaseTestCase

from . import postgres_tags


class TestCaseFunc(BaseTestCase):
    def test_pg_quote_escape_string_literal_sqlinjection(self):
        self.assertEqual(
            postgres_tags.pg_quote_escape_string_literal("mygoal' OR 1=1; DROP TABLE goals; SELECT 'a"),
            "'mygoal'' OR 1=1; DROP TABLE goals; SELECT ''a'",
        )

    def test_pg_quote_escape_string_literal_percent(self):
        self.assertEqual(postgres_tags.pg_quote_escape_string_literal("goal with % signs"), "'goal with %% signs'")

    def test_pg_quote_escape_string_literal_ampersand(self):
        self.assertEqual(postgres_tags.pg_quote_escape_string_literal("goal with & signs"), "'goal with & signs'")


class TestCaseRender(BaseTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.template = django.template.Template(
            """
{% load postgres_tags %}
CASE WHEN goal_id={{ goal_id|pg_quote_escape_string_literal }} THEN 1 ELSE 0
"""
        )

    def test_percent(self):
        self.assertEqual(
            self.template.render(django.template.Context({"goal_id": "goal with % signs"})).strip(),
            "CASE WHEN goal_id='goal with %% signs' THEN 1 ELSE 0",
        )

    def test_ampersand(self):
        self.assertEqual(
            self.template.render(django.template.Context({"goal_id": "goal with & signs"})).strip(),
            "CASE WHEN goal_id='goal with & signs' THEN 1 ELSE 0",
        )

    def test_sqlinjection(self):
        self.assertEqual(
            self.template.render(
                django.template.Context({"goal_id": "mygoal' OR 1=1; DROP TABLE goals; SELECT 'a"})
            ).strip(),
            "CASE WHEN goal_id='mygoal'' OR 1=1; DROP TABLE goals; SELECT ''a' THEN 1 ELSE 0",
        )
