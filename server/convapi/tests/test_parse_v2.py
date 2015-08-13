from django.test import TestCase

from convapi import parse_v2


class ParseReportTest(TestCase):

    def test_parse_header(self):
        complete_head = """
            # ----------------------------------------
            # All Web Site Data
            # Landing Pages
            # 20150416-20150416
            # ----------------------------------------
        """.strip().replace('\t', '')
        parser = parse_v2.CsvReport("")
        parser

    def test_parse_z11z_keyword(self):
        pass

    def test_parse_landing_page(self):
        pass

    def test_get_goal_name(self):
        pass

    def test_parse_goals(self):
        pass

    def test_parse(self):
        pass
