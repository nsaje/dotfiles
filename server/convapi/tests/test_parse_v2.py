#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import traceback

from convapi import exc
from mock import patch
from django.test import TestCase

from convapi import parse_v2

from utils import csv_utils


@patch('reports.redshift._get_cursor')
class ParseReportTest(TestCase):

    fixtures = ['test_ga_aggregation.yaml']

    def test_parse_header(self, cursor):
        complete_head = """
# ----------------------------------------
# All Web Site Data
# Landing Pages
# 20150416-20150416
# ----------------------------------------

Landing Page,Device Category,Sessions
""".strip().replace('\t', '')
        parser = parse_v2.GAReport("")
        try:
            parser._parse_header(complete_head.split('\n'))
        except:
            self.fail('Should not raise an exception {stack}'.format(
                stack=traceback.format_exc())
            )

        complete_head = """
# ----------------------------------------
# All Web Site Data
# Landing Pages
# 20150416-20150416
# ----------------------------------------

Device Category,Landing Page,Sessions
""".strip().replace('\t', '')
        parser = parse_v2.GAReport("")
        try:
            parser._parse_header(complete_head.split('\n'))
        except:
            self.fail('Should not raise an exception {stack}'.format(
                stack=traceback.format_exc())
            )

        complete_head = """
# ----------------------------------------
# All Web Site Data
# Landing Pages
# 20150416-20150416
# ----------------------------------------

Device Category,Sessions,Keyword
""".strip().replace('\t', '')
        parser = parse_v2.GAReport("")
        try:
            parser._parse_header(complete_head.split('\n'))
        except:
            self.fail('Should not raise an exception {stack}'.format(
                stack=traceback.format_exc())
            )

        complete_head = """
# ----------------------------------------
# All Web Site Data
# Landing Pages
# 20150416-20150416
# ----------------------------------------

"Device, Category","Landing Page","Sessions"
""".strip().replace('\t', '')
        parser = parse_v2.GAReport("")
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

        incomplete_head_3 = """
 ----------------------------------------



 ----------------------------------------""".strip().replace('\t', '')
        with self.assertRaises(exc.CsvParseException):
            parser._parse_header(incomplete_head_3.split('\n'))

        incomplete_head_4 = """
# ----------------------------------------



# ----------------------------------------""".strip().replace('\t', '')
        with self.assertRaises(exc.CsvParseException):
            parser._parse_header(incomplete_head_4.split('\n'))

        invalid_date_head = """
# ----------------------------------------
# All Web Site Data
# Landing Pages
# 20150416-20150417
# ----------------------------------------

Landing Page,Device Category,Sessions
""".strip().replace('\t', '')
        parser = parse_v2.GAReport("")
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
        parser = parse_v2.GAReport("")
        with self.assertRaises(exc.CsvParseException):
            parser._parse_header(invalid_date_head_1.split('\n'))

    def test_parse_z11z_keyword(self, cursor):
        parser = parse_v2.GAReport("")

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

    def test_parse_landing_page(self, cursor):
        parser = parse_v2.GAReport("")

        # some valid cases
        landing_page = "/commandnconquer/f05c20fc-d7e6-42b3-86c6-d8327599c96e/?v=5&_z1_adgid=890&_z1_caid=55310&_z1_msid=b1_gumgum"
        caid, src_par = parser._parse_landing_page(landing_page)
        self.assertEqual(55310, caid)
        self.assertEqual('b1_gumgum', src_par)

        landing_page = "/commandnconquer/f05c20fc-d7e6-42b3-86c6-d8327599c96e/?v=5&_z1_adgid=890&_z1_caid=55310&_z1_msid=b1_gumgum?referrer=www.zemanta.com"
        caid, src_par = parser._parse_landing_page(landing_page)
        self.assertEqual(55310, caid)
        self.assertEqual('b1_gumgum', src_par)

        landing_page = "/commandnconquer/f05c20fc-d7e6-42b3-86c6-d8327599c96e/?v=5&_z1_adgid=890&_z1_msid=b1_gumgum&_z1_caid=55310?referrer=www.zemanta.com"
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

    def test_get_goal_name(self, cursor):
        parser = parse_v2.GAReport("")

        goal_name = "Yell Free Listings (Goal 1 Conversion Rate)"
        self.assertEqual("Yell Free Listings", parser._get_goal_name(goal_name))

        goal_name = "Yell Free Listings (Goal 1 Completions)"
        self.assertEqual("Yell Free Listings", parser._get_goal_name(goal_name))

        goal_name = "Yell Free Listings (Goal 2 Value)"
        self.assertEqual("Yell Free Listings", parser._get_goal_name(goal_name))

    def test_get_goal_name_1(self, cursor):
        parser = parse_v2.GAReport("")
        goal_name = "*Lead: Whitepaper (Content Fact Sheet) (Goal 1 Conversion Rate)"
        self.assertEqual("*Lead: Whitepaper (Content Fact Sheet)", parser._get_goal_name(goal_name))

        goal_name = "*Lead: Whitepaper (Content Fact Sheet) (Goal 1 Completions)"
        self.assertEqual("*Lead: Whitepaper (Content Fact Sheet)", parser._get_goal_name(goal_name))

        goal_name = "*Lead: Whitepaper (Content Fact Sheet) (Goal 1 Value)"
        self.assertEqual("*Lead: Whitepaper (Content Fact Sheet)", parser._get_goal_name(goal_name))

    def test_parse_goals(self, cursor):
        parser = parse_v2.GAReport("")

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

        row_dict = {
            "Ecommerce Conversion Rate": "2%",
            "Transactions": "5",
            "Revenue": "$123"
        }
        resp = parser._parse_goals(row_dict.keys(), row_dict)
        self.assertEqual(5, resp['Goal 1']['conversions'])
        self.assertEqual("2%", resp['Goal 1']['conversion_rate'])
        self.assertEqual("$123", resp['Goal 1']['value'])

    def test_parse_unnamed_goals(self, cursor):
        parser = parse_v2.GAReport("")

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

    def test_merge(self, cursor):
        # GA report can potentially contain multiple entries for a single
        # content ad
        complete_csv = """
# ----------------------------------------
# All Web Site Data
# Landing Pages
# 20150416-20150416
# ----------------------------------------

Landing Page,Device Category,Sessions,Goal Completions
/unexpected-scenario?_z1_adgid=1&_z1_caid=1&_z1_msid=yahoo,desktop,6,1
/unexpected-scenario?_z1_adgid=1&_z1_caid=1&_z1_msid=yahoo,mobile,6,2
/unexpected-scenario?_z1_adgid=1&_z1_caid=1&_z1_msid=yahoo,tablet,6,3
,,600,96.33%,578,95.50%,1.06,00:00:10,0.00%,0,A$0.00

Day Index,Sessions
4/16/15,18
,18
""".strip().replace('\t', '')

        parser = parse_v2.GAReport(complete_csv)
        parser.parse()
        parser.validate()
        self.assertEqual(1, len(parser.entries))
        self.assertEqual(6, parser.valid_entries()[0].goals['Goal 1']['conversions'], 6)

        parser._check_session_counts()

        self.assertTrue(parser.is_media_source_specified())
        self.assertTrue(parser.is_content_ad_specified())


class OmnitureReportTest(TestCase):

    def test_parse_header(self):
        csv_header = """
,,,,,,,,,,
AdobeÂ® Scheduled Report,,,,,,,,,,
Report Suite: Global,,,,,,,,,,
Date: Sun. 19 Apr. 2015,,,,,,,,,,
Segment: All Visits (No Segment),,,,,,,,,,
,,,,,,,,,,""".strip().decode('utf-8')
        report = parse_v2.OmnitureReport(csv_utils.convert_to_xls(csv_header))
        report.parse()
        self.assertEqual(datetime.date(2015, 04, 19), report.get_date())
        self.assertTrue(report.is_empty())

    def test_extract_date(self):
        csv_header = """
,,,,,,,,,,
AdobeÂ® Scheduled Report,,,,,,,,,,
Report Suite: Global,,,,,,,,,,
Date: Sun. 19 Apr. 2015 2015-04-19 00:00:00,,,,,,,,,,
Segment: All Visits (No Segment),,,,,,,,,,
,,,,,,,,,,""".strip().decode('utf-8')
        report = parse_v2.OmnitureReport(csv_utils.convert_to_xls(csv_header))
        report.parse()
        self.assertEqual(datetime.date(2015, 04, 19), report.get_date())

        csv_header = """
,,,,,,,,,,
AdobeÂ® Scheduled Report,,,,,,,,,,
Report Suite: Global,,,,,,,,,,
Segment: All Visits (No Segment),,,,,,,,,,
,,,,,,,,,,""".strip().decode('utf-8')
        report = parse_v2.OmnitureReport(csv_utils.convert_to_xls(csv_header))
        with self.assertRaises(Exception):
            report.parse()

    def test_session_counts(self):
        pass

    def test_parse(self):
        pass
