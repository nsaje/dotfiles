import traceback

from convapi import exc
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

Landing Page,Device Category,Sessions
""".strip().replace('\t', '')
        parser = parse_v2.CsvReport("")
        try:
            parser._parse_header(complete_head.split('\n'))
        except:
           self.fail('Should not raise an exception {stack}'.format(
               stack=traceback.format_exc())
           )

        incomplete_head_1 = """
# ----------------------------------------
# ----------------------------------------""".strip().replace('\t', '')
        with self.assertRaises(exc.CsvParseException):
            parser._parse_header(incomplete_head_1.split('\n'))


        incomplete_head_2 = """
$ ----------------------------------------""".strip().replace('\t', '')
        with self.assertRaises(exc.CsvParseException):
            parser._parse_header(incomplete_head_2.split('\n'))


        invalid_date_head = """
# ----------------------------------------
# All Web Site Data
# Landing Pages
# 20150416-20150417
# ----------------------------------------

Landing Page,Device Category,Sessions
""".strip().replace('\t', '')
        parser = parse_v2.CsvReport("")
        with self.assertRaises(exc.CsvParseException):
            parser._parse_header(invalid_date_head.split('\n'))

        invalid_date_head_1 = """
# ----------------------------------------
# All Web Site Data
# Landing Pages
# 201504ab-20150417
# ----------------------------------------

Landing Page,Device Category,Sessions
""".strip().replace('\t', '')
        parser = parse_v2.CsvReport("")
        with self.assertRaises(exc.CsvParseException):
            parser._parse_header(invalid_date_head_1.split('\n'))

    def test_parse_z11z_keyword(self):
        parser = parse_v2.CsvReport("")

        # some valid cases

        keyword = 'z12341b1_gumgum1z'
        caid, src_par = parser._parse_z11z_keyword(keyword)
        self.assertEqual(2341, caid)
        self.assertEqual('b1_gumgum', src_par)

        keyword = 'z1z12341b1_gumgum1z'
        caid, src_par = parser._parse_z11z_keyword(keyword)
        self.assertEqual(2341, caid)
        self.assertEqual('b1_gumgum', src_par)

        keyword = 'z1z12341b1_gumgum1z1z'
        caid, src_par = parser._parse_z11z_keyword(keyword)
        self.assertEqual(2341, caid)
        self.assertEqual('b1_gumgum', src_par)

        keyword = 'more data here z12341b1_gumgum1z and even more here z1'
        caid, src_par = parser._parse_z11z_keyword(keyword)
        self.assertEqual(2341, caid)
        self.assertEqual('b1_gumgum', src_par)

        # some invalid cases

        keyword = ''
        caid, src_par = parser._parse_z11z_keyword(keyword)
        self.assertIsNone(caid)
        self.assertEqual('', src_par)

        # no caid
        keyword = 'z1asdfsadfasdhjkl1z'
        caid, src_par = parser._parse_z11z_keyword(keyword)
        self.assertIsNone(caid)
        self.assertEqual('', src_par)

        # no media source
        keyword = 'z112351z'
        caid, src_par = parser._parse_z11z_keyword(keyword)
        self.assertIsNone(caid)
        self.assertEqual('', src_par)


    def test_parse_landing_page(self):
        parser = parse_v2.CsvReport("")

        # some valid cases
        landing_page = "/commandnconquer/f05c20fc-d7e6-42b3-86c6-d8327599c96e/?v=5&_z1_adgid=890&_z1_caid=55310&_z1_msid=b1_gumgum"
        caid, src_par = parser._parse_landing_page(landing_page)
        self.assertEqual(55310, caid)
        self.assertEqual('b1_gumgum', src_par)

        # some invalid cases

        landing_page = "/commandnconquer/f05c20fc-d7e6-42b3-86c6-d8327599c96e/?v=5&_z1_adgid=890&_z1_caid=&_z1_msid=b1_gumgum"
        caid, src_par = parser._parse_landing_page(landing_page)
        self.assertIsNone(caid)
        self.assertEqual('', src_par)

        landing_page = "/commandnconquer/f05c20fc-d7e6-42b3-86c6-d8327599c96e/?v=5&_z1_adgid=890&_z1_msid=b1_gumgum"
        caid, src_par = parser._parse_landing_page(landing_page)
        self.assertIsNone(caid)
        self.assertEqual('', src_par)

        landing_page = "/commandnconquer/f05c20fc-d7e6-42b3-86c6-d8327599c96e/?v=5&_z1_adgid=890&_z1_caid="
        caid, src_par = parser._parse_landing_page(landing_page)
        self.assertIsNone(caid)
        self.assertEqual('', src_par)

    def test_get_goal_name(self):
        pass

    def test_parse_goals(self):
        pass

    def test_parse(self):
        pass
