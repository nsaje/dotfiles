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
        parser = parse_v2.CsvReport("")

        goal_name = "Yell Free Listings (Goal 1 Conversion Rate)"
        self.assertEqual("Yell Free Listings", parser._get_goal_name(goal_name))

        goal_name = "Yell Free Listings (Goal 1 Completions)"
        self.assertEqual("Yell Free Listings", parser._get_goal_name(goal_name))

        goal_name = "Yell Free Listings (Goal 2 Value)"
        self.assertEqual("Yell Free Listings", parser._get_goal_name(goal_name))

    def test_get_goal_name_1(self):
        parser = parse_v2.CsvReport("")
        goal_name = "*Lead: Whitepaper (Content Fact Sheet) (Goal 1 Conversion Rate)"
        self.assertEqual("*Lead: Whitepaper (Content Fact Sheet)", parser._get_goal_name(goal_name))

        goal_name = "*Lead: Whitepaper (Content Fact Sheet) (Goal 1 Completions)"
        self.assertEqual("*Lead: Whitepaper (Content Fact Sheet)", parser._get_goal_name(goal_name))

        goal_name = "*Lead: Whitepaper (Content Fact Sheet) (Goal 1 Value)"
        self.assertEqual("*Lead: Whitepaper (Content Fact Sheet)", parser._get_goal_name(goal_name))

    def test_parse_goals(self):
        parser = parse_v2.CsvReport("")

        row_dict = {
            "Yell Free Listings (Goal 1 Conversion Rate)": "2%",
            "Yell Free Listings (Goal 1 Completions)": "5",
            "Yell Free Listings (Goal 2 Value)": "$123"
        }
        resp = parser._parse_goals(row_dict.keys(), row_dict)
        self.assertEqual(5, resp['Yell Free Listings']['conversions'])
        self.assertEqual("2%", resp['Yell Free Listings']['conversion_rate'])
        self.assertEqual("$123", resp['Yell Free Listings']['value'])

        row_dict = {
            "Goal Conversion Rate": "2%",
            "Goal Completions": "5",
            "Goal Value": "$123"
        }
        resp = parser._parse_goals(row_dict.keys(), row_dict)
        self.assertEqual(5, resp['Goal 1']['conversions'])
        self.assertEqual("2%", resp['Goal 1']['conversion_rate'])
        self.assertEqual("$123", resp['Goal 1']['value'])

    def test_parse_unnamed_goals(self):
        parser = parse_v2.CsvReport("")

        fields_raw = "Landing Page,Device Category,Sessions,% New Sessions,New Users,Bounce Rate,Pages / Session,Avg. Session Duration"
        self.assertEqual([], parser._get_goal_fields(fields_raw.split(',')))

        fields_raw = "Landing Page,Device Category,Sessions,% New Sessions,New Users,Bounce Rate,Pages / Session,Avg. Session Duration,Ecommerce Conversion Rate,Transactions,Revenue"
        self.assertEqual(["Ecommerce Conversion Rate", "Transactions", "Revenue"], parser._get_goal_fields(fields_raw.split(',')))

        fields_raw = "Landing Page,Device Category,Sessions,% New Sessions,New Users,Bounce Rate,Pages / Session,Avg. Session Duration,Goal Conversion Rate,Goal Completions,Goal Value"
        self.assertEqual(["Goal Conversion Rate", "Goal Completions", "Goal Value"], parser._get_goal_fields(fields_raw.split(',')))

        fields_raw = "Landing Page,Device Category,Sessions,% New Sessions,New Users,Bounce Rate,Pages / Session,Avg. Session Duration,Pageviews,ToS"
        self.assertEqual([], parser._get_goal_fields(fields_raw.split(',')))

        fields_raw = "Landing Page,Device Category,Sessions,% New Sessions,New Users,Bounce Rate,Pages / Session,Avg. Session Duration,Transactions,Revenue,Ecommerce Conversion Rate"
        self.assertEqual(set(["Ecommerce Conversion Rate", "Transactions", "Revenue"]), set(parser._get_goal_fields(fields_raw.split(','))))

        fields_raw = "Landing Page,Device Category,Sessions,% New Sessions,New Users,Bounce Rate,Pages/Session,Avg. Session Duration,Goal Conversion Rate,Goal Completions,Goal Value"
        self.assertEqual(set(["Goal Conversion Rate", "Goal Completions", "Goal Value"]), set(parser._get_goal_fields(fields_raw.split(','))))

        fields_raw = "Landing Page,Sessions,% New Sessions,New Users,Bounce Rate,Pages / Session,Avg. Session Duration,Goal Conversion Rate,Goal Completions,Goal Value"
        self.assertEqual(set(["Goal Conversion Rate", "Goal Completions", "Goal Value"]), set(parser._get_goal_fields(fields_raw.split(','))))

        fields_raw = "Landing Page,Sessions,% New Sessions,New Users,Bounce Rate,Pages / Session,Avg. Session Duration,Revenue"
        self.assertEqual(set(["Revenue"]), set(parser._get_goal_fields(fields_raw.split(','))))

    def test_parse(self):
        pass
