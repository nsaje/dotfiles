#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import json
import traceback

from convapi import exc
from mock import patch, MagicMock
from django.test import TestCase

from convapi import parse_v2

from utils import csv_utils


@patch('reports.redshift.get_cursor')
class ParseReportTest(TestCase):

    fixtures = ['test_ga_aggregation.yaml']

    def test_report_utils(self, cursor):
        self.assertEqual(10, parse_v2._report_atoi("10"))
        self.assertEqual(None, parse_v2._report_atoi('#DIV/0'))

        self.assertEqual(0.0, parse_v2._report_atof("0.0"))
        self.assertEqual(None, parse_v2._report_atof('#DIV/0'))

    def test_parse_header(self, cursor):
        complete_head = """
# ----------------------------------------
# All Web Site Data
# Landing Pages
# 20150416-20150416
# ----------------------------------------

Landing Page,Device Category,Sessions
""".strip().replace('\t', '')
        parser = parse_v2.GAReportFromCSV("")
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
        parser = parse_v2.GAReportFromCSV("")
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
        parser = parse_v2.GAReportFromCSV("")
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
        parser = parse_v2.GAReportFromCSV("")
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
        parser = parse_v2.GAReportFromCSV("")
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
        parser = parse_v2.GAReportFromCSV("")
        with self.assertRaises(exc.CsvParseException):
            parser._parse_header(invalid_date_head_1.split('\n'))

    def test_parse_z11z_keyword(self, cursor):
        parser = parse_v2.GAReportFromCSV("")

        # some valid cases

        keyword = 'z12341b1_gumgum1z'
        caid, src_par, pub_par = parser._parse_z11z_keyword(keyword)
        self.assertEqual(2341, caid)
        self.assertEqual('b1_gumgum', src_par)
        self.assertEqual('', pub_par)

        keyword = 'z1z12341b1_gumgum1z'
        caid, src_par, pub_par = parser._parse_z11z_keyword(keyword)
        self.assertEqual(2341, caid)
        self.assertEqual('b1_gumgum', src_par)
        self.assertEqual('', pub_par)

        keyword = 'z1z12341b1_gumgum1z1z'
        caid, src_par, pub_par = parser._parse_z11z_keyword(keyword)
        self.assertEqual(2341, caid)
        self.assertEqual('b1_gumgum', src_par)
        self.assertEqual('', pub_par)

        keyword = 'more data here z12341b1_gumgum1z and even more here z1'
        caid, src_par, pub_par = parser._parse_z11z_keyword(keyword)
        self.assertEqual(2341, caid)
        self.assertEqual('b1_gumgum', src_par)
        self.assertEqual('', pub_par)

        # valid cases with publishers
        keyword = 'more data here z12341b1_gumgum__publisher.com1z and even more here z1'
        caid, src_par, pub_par = parser._parse_z11z_keyword(keyword)
        self.assertEqual(2341, caid)
        self.assertEqual('b1_gumgum', src_par)
        self.assertEqual('publisher.com', pub_par)

        keyword = 'more data here z12341b1_gumgum__publisher%2ecom1z and even more here z1'
        caid, src_par, pub_par = parser._parse_z11z_keyword(keyword)
        self.assertEqual(2341, caid)
        self.assertEqual('b1_gumgum', src_par)
        self.assertEqual('publisher.com', pub_par)

        keyword = 'more data here z12341b1_gumgum__publisher%20yeah1z and even more here z1'
        caid, src_par, pub_par = parser._parse_z11z_keyword(keyword)
        self.assertEqual(2341, caid)
        self.assertEqual('b1_gumgum', src_par)
        self.assertEqual('publisher yeah', pub_par)

        # some invalid cases

        keyword = ''
        caid, src_par, pub_par = parser._parse_z11z_keyword(keyword)
        self.assertIsNone(caid)
        self.assertEqual('', src_par)
        self.assertEqual('', pub_par)

        # no caid
        keyword = 'z1asdfsadfasdhjkl1z'
        caid, src_par, pub_par = parser._parse_z11z_keyword(keyword)
        self.assertIsNone(caid)
        self.assertEqual('', src_par)
        self.assertEqual('', pub_par)

        keyword = 'z1asdfsadfasdhjkl__publisher.com1z'
        caid, src_par, pub_par = parser._parse_z11z_keyword(keyword)
        self.assertIsNone(caid)
        self.assertEqual('', src_par)
        self.assertEqual('', pub_par)

        # no media source
        keyword = 'z11235__publisher.com1z'
        caid, src_par, pub_par = parser._parse_z11z_keyword(keyword)
        self.assertIsNone(caid)
        self.assertEqual('', src_par)
        self.assertEqual('', pub_par)

    def test_parse_landing_page(self, cursor):
        parser = parse_v2.GAReportFromCSV("")

        # some valid cases
        landing_page = "/commandnconquer/f05c20fc-d7e6-42b3-86c6-d8327599c96e/?v=5&_z1_adgid=890&_z1_caid=55310&_z1_msid=b1_gumgum&_z1_pub=www.test.com&"
        caid, src_par, pub = parser._parse_landing_page(landing_page)
        self.assertEqual(55310, caid)
        self.assertEqual('b1_gumgum', src_par)
        self.assertEqual('www.test.com', pub)

        landing_page = "/commandnconquer/f05c20fc-d7e6-42b3-86c6-d8327599c96e/?v=5&_z1_adgid=890&_z1_caid=55310&_z1_msid=b1_gumgum"
        caid, src_par, pub = parser._parse_landing_page(landing_page)
        self.assertEqual(55310, caid)
        self.assertEqual('b1_gumgum', src_par)
        self.assertEqual('', pub)

        landing_page = "/commandnconquer/f05c20fc-d7e6-42b3-86c6-d8327599c96e/?v=5&_z1_adgid=890&_z1_caid=55310&_z1_msid=b1_gumgum&_z1_pub=www.test.com&?referrer=www.zemanta.com"
        caid, src_par, pub = parser._parse_landing_page(landing_page)
        self.assertEqual(55310, caid)
        self.assertEqual('b1_gumgum', src_par)
        self.assertEqual('www.test.com', pub)

        landing_page = "/commandnconquer/f05c20fc-d7e6-42b3-86c6-d8327599c96e/?v=5&_z1_adgid=890&_z1_caid=55310&_z1_msid=b1_gumgum&_z1_pub=www%2Etest%2ecom&?referrer=www.zemanta.com"
        caid, src_par, pub = parser._parse_landing_page(landing_page)
        self.assertEqual(55310, caid)
        self.assertEqual('b1_gumgum', src_par)
        self.assertEqual('www.test.com', pub)

        landing_page = "/commandnconquer/f05c20fc-d7e6-42b3-86c6-d8327599c96e/?v=5&_z1_adgid=890&_z1_pub=95%25+iOs&&_z1_msid=b1_gumgum&_z1_caid=55310?referrer=www.zemanta.com"
        caid, src_par, pub = parser._parse_landing_page(landing_page)
        self.assertEqual(55310, caid)
        self.assertEqual('b1_gumgum', src_par)
        self.assertEqual('95% iOs', pub)

        # some invalid cases

        landing_page = "/commandnconquer/f05c20fc-d7e6-42b3-86c6-d8327599c96e/?v=5&_z1_adgid=890&_z1_caid=&_z1_msid=b1_gumgum&_z1_pub=www.test.com&"
        caid, src_par, pub = parser._parse_landing_page(landing_page)
        self.assertIsNone(caid)
        self.assertEqual('', src_par, '')
        self.assertEqual('', pub)

        landing_page = "/commandnconquer/f05c20fc-d7e6-42b3-86c6-d8327599c96e/?v=5&_z1_adgid=890&_z1_msid=b1_gumgum&_z1_pub=www.test.com&"
        caid, src_par, pub = parser._parse_landing_page(landing_page)
        self.assertIsNone(caid)
        self.assertEqual('', src_par, '')
        self.assertEqual('', pub)

        landing_page = "/commandnconquer/f05c20fc-d7e6-42b3-86c6-d8327599c96e/?v=5&_z1_adgid=890&_z1_caid=&_z1_pub=www.test.com&"
        caid, src_par, pub = parser._parse_landing_page(landing_page)
        self.assertIsNone(caid)
        self.assertEqual('', src_par, '')
        self.assertEqual('', pub)

    def test_get_goal_name(self, cursor):
        parser = parse_v2.GAReportFromCSV("")

        goal_name = "Yell Free Listings (Goal 1 Conversion Rate)"
        self.assertEqual("Yell Free Listings", parser._get_goal_name(goal_name))

        goal_name = "Yell Free Listings (Goal 1 Completions)"
        self.assertEqual("Yell Free Listings", parser._get_goal_name(goal_name))

        goal_name = "Yell Free Listings (Goal 2 Value)"
        self.assertEqual("Yell Free Listings", parser._get_goal_name(goal_name))

    def test_get_goal_name_1(self, cursor):
        parser = parse_v2.GAReportFromCSV("")
        goal_name = "*Lead: Whitepaper (Content Fact Sheet) (Goal 1 Conversion Rate)"
        self.assertEqual("*Lead: Whitepaper (Content Fact Sheet)", parser._get_goal_name(goal_name))

        goal_name = "*Lead: Whitepaper (Content Fact Sheet) (Goal 1 Completions)"
        self.assertEqual("*Lead: Whitepaper (Content Fact Sheet)", parser._get_goal_name(goal_name))

        goal_name = "*Lead: Whitepaper (Content Fact Sheet) (Goal 1 Value)"
        self.assertEqual("*Lead: Whitepaper (Content Fact Sheet)", parser._get_goal_name(goal_name))

    def test_parse_goals(self, cursor):
        parser = parse_v2.GAReportFromCSV("")

        row_dict = {
            "Yell Free Listings (Goal 1 Conversion Rate)": "2%",
            "Yell Free Listings (Goal 1 Completions)": "5",
            "Yell Free Listings (Goal 2 Value)": "$123"
        }
        resp = parser._parse_goals(row_dict.keys(), row_dict)
        self.assertEqual(5, resp['Yell Free Listings'])

        row_dict = {
            "Goal Conversion Rate": "2%",
            "Goal Completions": "5",
            "Goal Value": "$123"
        }
        resp = parser._parse_goals(row_dict.keys(), row_dict)
        self.assertEqual(5, resp[parse_v2.DEFAULT_GOAL_NAME])

        row_dict = {
            "Ecommerce Conversion Rate": "2%",
            "Transactions": "5",
            "Revenue": "$123"
        }
        resp = parser._parse_goals(row_dict.keys(), row_dict)
        self.assertEqual(5, resp[parse_v2.DEFAULT_GOAL_NAME])

    def test_parse_goals_unnamed(self, cusrsor):
        parser = parse_v2.GAReportFromCSV("")

        row_dict = {
            "Goal Conversion Rate": "2%",
            "Goal Completions": "5",
            "Goal Value": "$123"
        }
        resp = parser._parse_goals(row_dict.keys(), row_dict)
        self.assertEqual(5, resp[parse_v2.DEFAULT_GOAL_NAME])

        row_dict = {
            "Goal Conversion Rate": "2%",
            "Goal Completions": "5",
            "Goal Value": "$123",
            "Goal Conversion Rate 1": "2%",
            "Goal Completions 1": "5",
            "Goal Value 1": "$123"
        }
        with self.assertRaises(exc.CsvParseException):
            parser._parse_goals(row_dict.keys(), row_dict)

    def test_parse_unnamed_goals(self, cursor):
        parser = parse_v2.GAReportFromCSV("")

        fields_raw = "Landing Page,Device Category,Sessions,% New Sessions,New Users,Bounce Rate,Pages / Session,Avg. Session Duration"
        self.assertEqual([], parser._get_conversion_goal_fields(fields_raw.split(',')))

        fields_raw = "Landing Page,Device Category,Sessions,% New Sessions,New Users,Bounce Rate,Pages / Session,Avg. Session Duration,Ecommerce Conversion Rate,Transactions,Revenue"
        self.assertEqual(["Transactions"], parser._get_conversion_goal_fields(fields_raw.split(',')))

        fields_raw = "Landing Page,Device Category,Sessions,% New Sessions,New Users,Bounce Rate,Pages / Session,Avg. Session Duration,Goal Conversion Rate,Goal Completions,Goal Value"
        self.assertEqual(["Goal Completions"], parser._get_conversion_goal_fields(fields_raw.split(',')))

        fields_raw = "Landing Page,Device Category,Sessions,% New Sessions,New Users,Bounce Rate,Pages / Session,Avg. Session Duration,Pageviews,ToS"
        self.assertEqual([], parser._get_conversion_goal_fields(fields_raw.split(',')))

        fields_raw = "Landing Page,Device Category,Sessions,% New Sessions,New Users,Bounce Rate,Pages / Session,Avg. Session Duration,Transactions,Revenue,Ecommerce Conversion Rate"
        self.assertEqual(set(["Transactions"]), set(parser._get_conversion_goal_fields(fields_raw.split(','))))

        fields_raw = "Landing Page,Device Category,Sessions,% New Sessions,New Users,Bounce Rate,Pages/Session,Avg. Session Duration,Goal Conversion Rate,Goal Completions,Goal Value"
        self.assertEqual(set(["Goal Completions"]), set(parser._get_conversion_goal_fields(fields_raw.split(','))))

        fields_raw = "Landing Page,Sessions,% New Sessions,New Users,Bounce Rate,Pages / Session,Avg. Session Duration,Goal Conversion Rate,Goal Completions,Goal Value"
        self.assertEqual(set(["Goal Completions"]), set(parser._get_conversion_goal_fields(fields_raw.split(','))))

        fields_raw = "Landing Page,Sessions,% New Sessions,New Users,Bounce Rate,Pages / Session,Avg. Session Duration,Revenue"
        self.assertEqual(set([]), set(parser._get_conversion_goal_fields(fields_raw.split(','))))

    def test_missing_columns(self, cursor):
        # GA report can potentially contain multiple entries for a single
        # content ad
        complete_csv = """
# ----------------------------------------
# All Web Site Data
# Landing Pages
# 20150416-20150416
# ----------------------------------------

Landing Page,Device Category,Goal Completions
/unexpected-scenario?_z1_adgid=1&_z1_caid=1&_z1_msid=yahoo,desktop,6,1
,,600,96.33%,578,95.50%,1.06,00:00:10,0.00%,0,A$0.00

Day Index,Sessions
4/16/15,18
,18
""".strip().replace('\t', '')

        with self.assertRaises(exc.CsvParseException):
            parser = parse_v2.GAReportFromCSV(complete_csv)
            parser.parse()

    def test_merge(self, cursor):
        # GA report can potentially contain multiple entries for a single
        # content ad
        complete_csv = """
# ----------------------------------------,,,,,,,
# All Web Site Data
# Landing Pages
# 20150416-20150416
# ----------------------------------------,,,,,,,
,,,,,,,
Landing Page,Device Category,Sessions,Goal Completions,% New Sessions,Avg. Session Duration,Pages / Session,Bounce Rate,New Users
/unexpected-scenario?_z1_adgid=1&_z1_caid=1&_z1_msid=yahoo&_z1_pub=www.test.com,desktop,6,1,0.00%,<00:00:00,1,1.00%,1
/unexpected-scenario?_z1_adgid=1&_z1_caid=1&_z1_msid=yahoo&_z1_pub=www.test.com,mobile,6,2,0.00%,00:00:00,1,1.00%,1
/unexpected-scenario?_z1_adgid=1&_z1_caid=1&_z1_msid=yahoo&_z1_pub=www.bar.com,tablet,6,3,0.00%,00:00:00,1,1.00%,1
,,600,96.33%,578,95.50%,1.06,00:00:10,0.00%,0,A$0.00
,,,,,,,
Day Index,Sessions
4/16/15,18
,18
""".strip().replace('\t', '')

        parser = parse_v2.GAReportFromCSV(complete_csv)
        parser.parse()
        parser.validate()
        self.assertEqual(2, len(parser.entries))

        # Content ads
        valid_entries = parser.get_content_ad_stats()
        self.assertEqual(6, valid_entries[0].goals[parse_v2.DEFAULT_GOAL_NAME])

        self.assertTrue(parser.is_media_source_specified())
        self.assertTrue(parser.is_content_ad_specified())

        entry = valid_entries[0]
        self.assertEqual(18, entry.visits)
        self.assertEqual(18, entry.pageviews)
        self.assertEqual(0.01, entry.bounce_rate)

        self.assertEqual(3, entry.new_visits)
        self.assertEqual(0, entry.bounced_visits)
        self.assertEqual(0, entry.total_time_on_site)

        self.assertEqual(1, entry.content_ad_id)
        self.assertEqual('yahoo', entry.source_param)
        self.assertEqual('2015-04-16', entry.report_date)

        self.assertEqual({parse_v2.DEFAULT_GOAL_NAME: 6}, entry.goals)

        # Publishers
        valid_entries = parser.get_publisher_stats()
        self.assertEqual(3, valid_entries[0].goals[parse_v2.DEFAULT_GOAL_NAME])

        self.assertTrue(parser.is_media_source_specified())
        self.assertTrue(parser.is_content_ad_specified())

        entry = valid_entries[0]
        self.assertEqual(12, entry.visits)
        self.assertEqual(12, entry.pageviews)
        self.assertEqual(0.01, entry.bounce_rate)

        self.assertEqual(2, entry.new_visits)
        self.assertEqual(0, entry.bounced_visits)
        self.assertEqual(0, entry.total_time_on_site)

        self.assertEqual(None, entry.content_ad_id)
        self.assertEqual(1, entry.ad_group_id)
        self.assertEqual("www.test.com", entry.publisher_param)
        self.assertEqual('yahoo', entry.source_param)
        self.assertEqual('2015-04-16', entry.report_date)

        self.assertEqual({parse_v2.DEFAULT_GOAL_NAME: 3}, entry.goals)


class OmnitureReportTest(TestCase):

    fixtures = ['test_ga_aggregation.yaml']

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
        csv_file = """
######################################################################
# Company:,Zemanta
# URL:,.
# Site:,Global
# Range:,Sat. 12 Sep. 2015
# Report:,Tracking Code Report
# Description:,""
######################################################################
# Report Options:
# Report Type: ,"Ranked"
# Selected Metrics: ,"Visits, New Sessions, Unique Visitors, Bounce Rate, Pages/Session, Avg. Session Duration, Entries, Bounces, Page Views, Total Seconds Spent"
# Broken Down by: ,"None"
# Data Filter: ,"RANDOM"
# Compare to Report Suite: ,"None"
# Compare to Segment: ,"None"
# Item Filter: ,"None"
# Percent Shown as: ,"Number"
# Segment: ,"All Visits (No Segment)"
######################################################################
#
# Copyright 2015 Adobe Systems Incorporated. All rights reserved.
# Use of this document signifies your agreement to the Terms of Use (http://marketing.adobe.com/resources/help/terms.html?type=prod&locale=en_US) and Online Privacy Policy (http://my.omniture.com/x/privacy).
# Adobe Systems Incorporated products and services are licensed under the following Netratings patents: 5675510 5796952 6115680 6108637 6138155 6643696 and 6763386.
#
######################################################################

,Tracking Code,Visits,,New Sessions,Unique Visitors,,Bounce Rate,Pages/Session,Avg. Session Duration,Entries,,Bounces,,Page Views,,Total Seconds Spent,
1.,CSY-PB-ZM-AB-M-outbrain:Gandalf-Is-Coming-Get-Ready-for-Winter-Storms,20,0.5%,100.00%,20,0.5%,100.0%,1.00,605:12:39,20,0.5%,20,0.6%,20,0.4%,0,0.0%
2.,CSY-PB-ZM-AB-M-yahoo:Gandalf-Is-Coming-Get-Ready-for-Winter-Storms,20,0.5%,100.00%,20,0.5%,100.0%,1.00,605:12:39,20,0.5%,20,0.6%,20,0.4%,0,0.0%
3.,CSY-PB-ZM-AB-M-b1_triplelift:Gandalf-Is-Coming-Get-Ready-for-Winter-Storms,20,0.5%,100.00%,20,0.5%,100.0%,1.00,605:12:39,20,0.5%,20,0.6%,20,0.4%,0,0.0%
,Total,20,0.5%,100.00%,20,0.5%,100.0%,1.00,605:12:39,20,0.5%,20,0.6%,20,0.4%,0,0.0%
""".strip().decode('utf-8')
        with self.assertRaises(exc.IncompleteReportException):
            report = parse_v2.OmnitureReport(csv_utils.convert_to_xls(csv_file))
            report.parse()

    def test_parse_invalid(self):
        csv_file = """
######################################################################
# Company:,Zemanta
# URL:,.
# Site:,Global
# Range:,Sat. 12 Sep. 2015
# Report:,Tracking Code Report
# Description:,""
######################################################################
# Report Options:
# Report Type: ,"Ranked"
# Selected Metrics: ,"Visits, New Sessions, Unique Visitors, Bounce Rate, Pages/Session, Avg. Session Duration, Entries, Bounces, Page Views, Total Seconds Spent"
# Broken Down by: ,"None"
# Data Filter: ,"RANDOM"
# Compare to Report Suite: ,"None"
# Compare to Segment: ,"None"
# Item Filter: ,"None"
# Percent Shown as: ,"Number"
# Segment: ,"All Visits (No Segment)"
######################################################################
#
# Copyright 2015 Adobe Systems Incorporated. All rights reserved.
# Use of this document signifies your agreement to the Terms of Use (http://marketing.adobe.com/resources/help/terms.html?type=prod&locale=en_US) and Online Privacy Policy (http://my.omniture.com/x/privacy).
# Adobe Systems Incorporated products and services are licensed under the following Netratings patents: 5675510 5796952 6115680 6108637 6138155 6643696 and 6763386.
#
######################################################################

,Tracking Code,Visits,,New Sessions,Unique Visitors,,Bounce Rate,Pages/Session,Avg. Session Duration,Entries,,Bounces,,Page Views,,Total Seconds Spent,
1.,CSY-PB-ZM-AB-M-z111z:Gandalf-Is-Coming-Get-Ready-for-Winter-Storms,10,0.5%,100.00%,20,0.5%,100.0%,1.00,605:12:39,20,0.5%,20,0.6%,40,0.4%,0,0.0%
,Total,10,0.5%,100.00%,20,0.5%,100.0%,1.00,605:12:39,20,0.5%,20,0.6%,40,0.4%,0,0.0%
""".strip().decode('utf-8')

        report = parse_v2.OmnitureReport(csv_utils.convert_to_xls(csv_file))
        report.parse()
        report.validate()

        self.assertFalse(all(entry.is_row_valid() for entry in report.entries.values()))

        source_specified, source_errors = report.is_media_source_specified()
        cad_specified, cad_errors = report.is_content_ad_specified()

        self.assertFalse(source_specified)
        blob = {
            "Pages/Session": "1.00",
            "New Sessions": "100.00%",
            "Bounce Rate": "100.0%",
            "Avg. Session Duration": "605:12:39",
            "Bounces": "20",
            "Visits": "10",
            "Tracking Code": "CSY-PB-ZM-AB-M-z111z:Gandalf-Is-Coming-Get-Ready-for-Winter-Storms",
            "Total Seconds Spent": "0",
            "Entries": "20",
            "Unique Visitors": "20",
            "Page Views": "40"
        }

        self.assertEqual(blob, json.loads(source_errors[0]))
        self.assertFalse(cad_specified)
        self.assertEqual(blob, json.loads(cad_errors[0]))

    def test_acceptable_deviation(self):
        report = parse_v2.OmnitureReport('')
        # no exeption should be raised, equal numbers
        report.entries = {1: MagicMock(visits=100)}
        report._check_session_counts({'Visits': '100'})

        # no exeption should be raised, inside acceptable absolute and relative deviation
        report.entries = {1: MagicMock(visits=101)}
        report._check_session_counts({'Visits': '100'})

        # no exeption should be raised, inside acceptable absolute deviation
        report.entries = {1: MagicMock(visits=105)}
        report._check_session_counts({'Visits': '100'})

        # no exeption should be raised, inside acceptable absolute deviation
        report.entries = {1: MagicMock(visits=110)}
        report._check_session_counts({'Visits': '100'})

        # no exeption should be raised, inside acceptable relative deviation
        report.entries = {1: MagicMock(visits=1020)}
        report._check_session_counts({'Visits': '1000'})

        # no exeption should be raised, inside acceptable relative deviation
        report.entries = {1: MagicMock(visits=1030)}
        report._check_session_counts({'Visits': '1000'})

        # outside of acceptable deviation (relative and absolute)
        report.entries = {1: MagicMock(visits=1040)}
        with self.assertRaisesRegexp(exc.IncompleteReportException, r'Number of total sessions'):
            report._check_session_counts({'Visits': '1000'})

        # always raise an exception if sum is less than total
        report.entries = {1: MagicMock(visits=1000)}
        with self.assertRaisesRegexp(exc.IncompleteReportException, r'Number of total sessions'):
            report._check_session_counts({'Visits': '1010'})

    def test_clean_goals(self):
        omniture_row_dict = {'Bounces': '123', 'Unique Visits': '12', 'Carts': '22', 'Visits': '11', 'Revenue': '31', 'Random': '1'}

        row = parse_v2.OmnitureReportRow(omniture_row_dict, datetime.date(2016, 1, 1), None, None, None, None)
        self.assertTrue(row.needs_goals_validation)
        self.assertDictEqual(row.goals, {
            'Carts': 22,
            'Revenue': 31,
            'Random': 1,
        })

        row.clean_goals(['Carts', 'Revenue'])
        self.assertDictEqual(row.goals, {
            'Carts': 22,
            'Revenue': 31,
        })

    def test_dont_clean_goals(self):
        omniture_row_dict = {'Bounces': '123', 'Unique Visits': '12', 'Carts (Event 12)': '22', 'Visits': '11', 'Revenue': '31', 'Random': '1'}

        row = parse_v2.OmnitureReportRow(omniture_row_dict, datetime.date(2016, 1, 1), None, None, None, None)
        self.assertFalse(row.needs_goals_validation)
        self.assertDictEqual(row.goals, {
            'Carts': 22,
        })

    def test_parse(self):
        csv_file = """
######################################################################
# Company:,Zemanta
# URL:,.
# Site:,Global
# Range:,Sat. 12 Sep. 2015
# Report:,Tracking Code Report
# Description:,""
######################################################################
# Report Options:
# Report Type: ,"Ranked"
# Selected Metrics: ,"Visits, New Sessions, Unique Visitors, Bounce Rate, Pages/Session, Avg. Session Duration, Entries, Bounces, Page Views, Total Seconds Spent"
# Broken Down by: ,"None"
# Data Filter: ,"RANDOM"
# Compare to Report Suite: ,"None"
# Compare to Segment: ,"None"
# Item Filter: ,"None"
# Percent Shown as: ,"Number"
# Segment: ,"All Visits (No Segment)"
######################################################################
#
# Copyright 2015 Adobe Systems Incorporated. All rights reserved.
# Use of this document signifies your agreement to the Terms of Use (http://marketing.adobe.com/resources/help/terms.html?type=prod&locale=en_US) and Online Privacy Policy (http://my.omniture.com/x/privacy).
# Adobe Systems Incorporated products and services are licensed under the following Netratings patents: 5675510 5796952 6115680 6108637 6138155 6643696 and 6763386.
#
######################################################################

,Tracking Code,Visits,,New Sessions,Unique Visitors,,Bounce Rate,Pages/Session,Avg. Session Duration,Entries,,Bounces,,Page Views,,Total Seconds Spent,,Test Event (Event 1),
1.,CSY-PB-ZM-AB-M-z11yahoo1z:Gandalf-Is-Coming-Get-Ready-for-Winter-Storms,10,0.5%,100.00%,20,0.5%,100.0%,1.00,605:12:39,20,0.5%,20,0.6%,40,0.4%,0,0.0%,5,50.0%
,Total,10,0.5%,100.00%,20,0.5%,100.0%,1.00,605:12:39,20,0.5%,20,0.6%,40,0.4%,0,0.0%,5,50.0%
""".strip().decode('utf-8')

        report = parse_v2.OmnitureReport(csv_utils.convert_to_xls(csv_file))
        report.parse()
        report.validate()

        self.assertTrue(all(entry.is_row_valid() for entry in report.entries.values()))

        self.assertEqual(datetime.date(2015, 9, 12), report.start_date)
        valid_entries = report.get_content_ad_stats()
        self.assertEqual(1, len(valid_entries))
        entry = valid_entries[0]

        self.assertEqual(10, entry.visits)
        self.assertEqual(40, entry.pageviews)
        self.assertEqual(1, entry.bounce_rate)
        self.assertEqual(20, entry.new_visits)
        self.assertEqual(10, entry.bounced_visits)
        self.assertEqual(0, entry.total_time_on_site)

        self.assertEqual(1, entry.content_ad_id)
        self.assertEqual('yahoo', entry.source_param)

        self.assertEqual('2015-09-12', entry.report_date)

        self.assertEqual({'Test Event': 5}, entry.goals)

    def test_parse_with_pubs(self):
        csv_file = """
######################################################################
# Company:,Zemanta
# URL:,.
# Site:,Global
# Range:,Sat. 12 Sep. 2015
# Report:,Tracking Code Report
# Description:,""
######################################################################
# Report Options:
# Report Type: ,"Ranked"
# Selected Metrics: ,"Visits, New Sessions, Unique Visitors, Bounce Rate, Pages/Session, Avg. Session Duration, Entries, Bounces, Page Views, Total Seconds Spent"
# Broken Down by: ,"None"
# Data Filter: ,"RANDOM"
# Compare to Report Suite: ,"None"
# Compare to Segment: ,"None"
# Item Filter: ,"None"
# Percent Shown as: ,"Number"
# Segment: ,"All Visits (No Segment)"
######################################################################
#
# Copyright 2015 Adobe Systems Incorporated. All rights reserved.
# Use of this document signifies your agreement to the Terms of Use (http://marketing.adobe.com/resources/help/terms.html?type=prod&locale=en_US) and Online Privacy Policy (http://my.omniture.com/x/privacy).
# Adobe Systems Incorporated products and services are licensed under the following Netratings patents: 5675510 5796952 6115680 6108637 6138155 6643696 and 6763386.
#
######################################################################

,Tracking Code,Visits,,New Sessions,Unique Visitors,,Bounce Rate,Pages/Session,Avg. Session Duration,Entries,,Bounces,,Page Views,,Total Seconds Spent,,Test Event (Event 1),
1.,CSY-PB-ZM-AB-M-z11yahoo__foo.com1z:Gandalf-Is-Coming-Get-Ready-for-Winter-Storms,10,0.5%,100.00%,20,0.5%,100.0%,1.00,605:12:39,20,0.5%,20,0.6%,40,0.4%,0,0.0%,5,50.0%
2.,CSY-PB-ZM-AB-MM-z11yahoo__bar.com1z:Gandalf-Is-Coming-Get-Ready-for-Winter-Storms,10,0.5%,100.00%,20,0.5%,100.0%,1.00,605:12:39,20,0.5%,20,0.6%,40,0.4%,0,0.0%,5,50.0%
3.,CSY-PB-ZM-AB-MM-z12yahoo__bar.com1z:Gandalf-Is-Coming-Get-Ready-for-Winter-Storms,20,0.5%,100.00%,20,0.5%,100.0%,1.00,605:12:39,20,0.5%,20,0.6%,40,0.4%,0,0.0%,5,50.0%
,Total,40,0.5%,100.00%,40,0.5%,100.0%,1.00,605:12:39,40,0.5%,40,0.6%,80,0.4%,0,0.0%,10,50.0%
""".strip().decode('utf-8')

        report = parse_v2.OmnitureReport(csv_utils.convert_to_xls(csv_file))
        report.parse()
        report.validate()

        self.assertTrue(all(entry.is_row_valid() for entry in report.entries.values()))
        self.assertTrue(all(entry.is_publisher_row_valid() for entry in report.entries.values()))

        self.assertEqual(datetime.date(2015, 9, 12), report.start_date)

        # Content ads
        valid_entries = report.get_content_ad_stats()
        self.assertEqual(2, len(valid_entries))
        entry = valid_entries[1]

        self.assertEqual(20, entry.visits)
        self.assertEqual(80, entry.pageviews)
        self.assertEqual(1, entry.bounce_rate)
        self.assertEqual(40, entry.new_visits)
        self.assertEqual(20, entry.bounced_visits)
        self.assertEqual(0, entry.total_time_on_site)

        self.assertEqual(1, entry.content_ad_id)
        self.assertEqual('yahoo', entry.source_param)
        self.assertEqual('2015-09-12', entry.report_date)

        self.assertEqual({'Test Event': 10}, entry.goals)

        # Publishers
        valid_entries = report.get_publisher_stats()
        self.assertEqual(2, len(valid_entries))
        entry = valid_entries[0]

        self.assertEqual(30, entry.visits)
        self.assertEqual(80, entry.pageviews)
        self.assertEqual(1, entry.bounce_rate)
        self.assertEqual(40, entry.new_visits)
        self.assertEqual(30, entry.bounced_visits)
        self.assertEqual(0, entry.total_time_on_site)

        self.assertEqual(1, entry.ad_group_id)
        self.assertEqual("bar.com", entry.publisher_param)
        self.assertEqual('yahoo', entry.source_param)
        self.assertEqual('2015-09-12', entry.report_date)

        self.assertEqual({'Test Event': 10}, entry.goals)

    def test_parse_no_tracking_code_header(self):
        csv_file = """
######################################################################
# Company:,Zemanta
# URL:,.
# Site:,Global
# Range:,Sat. 12 Sep. 2015
# Report:,Tracking Code Report
# Description:,""
######################################################################
# Report Options:
# Report Type: ,"Ranked"
# Selected Metrics: ,"Visits, New Sessions, Unique Visitors, Bounce Rate, Pages/Session, Avg. Session Duration, Entries, Bounces, Page Views, Total Seconds Spent"
# Broken Down by: ,"None"
# Data Filter: ,"RANDOM"
# Compare to Report Suite: ,"None"
# Compare to Segment: ,"None"
# Item Filter: ,"None"
# Percent Shown as: ,"Number"
# Segment: ,"All Visits (No Segment)"
######################################################################
#
# Copyright 2015 Adobe Systems Incorporated. All rights reserved.
# Use of this document signifies your agreement to the Terms of Use (http://marketing.adobe.com/resources/help/terms.html?type=prod&locale=en_US) and Online Privacy Policy (http://my.omniture.com/x/privacy).
# Adobe Systems Incorporated products and services are licensed under the following Netratings patents: 5675510 5796952 6115680 6108637 6138155 6643696 and 6763386.
#
######################################################################

,Some other thing,,Visits,,New Sessions,Unique Visitors,,Bounce Rate,Pages/Session,Avg. Session Duration,Entries,,Bounces,,Page Views,,Total Seconds Spent,,Test Event (Event 1),
1.,,CSY-PB-ZM-AB-M-z11yahoo1z:Gandalf-Is-Coming-Get-Ready-for-Winter-Storms,10,0.5%,100.00%,20,0.5%,100.0%,1.00,605:12:39,20,0.5%,20,0.6%,40,0.4%,0,0.0%,5,50.0%
,,Total,10,0.5%,100.00%,20,0.5%,100.0%,1.00,605:12:39,20,0.5%,20,0.6%,40,0.4%,0,0.0%,5,50.0%
""".strip().decode('utf-8')

        report = parse_v2.OmnitureReport(csv_utils.convert_to_xls(csv_file))
        report.parse()
        report.validate()

        self.assertTrue(all(entry.is_row_valid() for entry in report.entries.values()))

        self.assertEqual(datetime.date(2015, 9, 12), report.start_date)
        valid_entries = report.get_content_ad_stats()
        self.assertEqual(1, len(valid_entries))
        entry = valid_entries[0]

        self.assertEqual(10, entry.visits)
        self.assertEqual(40, entry.pageviews)
        self.assertEqual(1, entry.bounce_rate)
        self.assertEqual(20, entry.new_visits)
        self.assertEqual(10, entry.bounced_visits)
        self.assertEqual(0, entry.total_time_on_site)

        self.assertEqual(1, entry.content_ad_id)
        self.assertEqual('yahoo', entry.source_param)

        self.assertEqual('2015-09-12', entry.report_date)

        self.assertEqual({'Test Event': 5}, entry.goals)

    def test_parse_totals_under_header(self):
        csv_file = """
######################################################################
# Company:,Zemanta
# URL:,.
# Site:,Global
# Range:,Sat. 12 Sep. 2015
# Report:,Tracking Code Report
# Description:,""
######################################################################
# Report Options:
# Report Type: ,"Ranked"
# Selected Metrics: ,"Visits, New Sessions, Unique Visitors, Bounce Rate, Pages/Session, Avg. Session Duration, Entries, Bounces, Page Views, Total Seconds Spent"
# Broken Down by: ,"None"
# Data Filter: ,"RANDOM"
# Compare to Report Suite: ,"None"
# Compare to Segment: ,"None"
# Item Filter: ,"None"
# Percent Shown as: ,"Number"
# Segment: ,"All Visits (No Segment)"
######################################################################
#
# Copyright 2015 Adobe Systems Incorporated. All rights reserved.
# Use of this document signifies your agreement to the Terms of Use (http://marketing.adobe.com/resources/help/terms.html?type=prod&locale=en_US) and Online Privacy Policy (http://my.omniture.com/x/privacy).
# Adobe Systems Incorporated products and services are licensed under the following Netratings patents: 5675510 5796952 6115680 6108637 6138155 6643696 and 6763386.
#
######################################################################

,Some other thing,,Visits,,New Sessions,Unique Visitors,,Bounce Rate,Pages/Session,Avg. Session Duration,Entries,,Bounces,,Page Views,,Total Seconds Spent,,Test Event (Event 1),
1.,SOME_TOTALS,,20,0.5%,100.00%,20,0.5%,100.0%,1.00,605:12:39,20,0.5%,20,0.6%,40,0.4%,0,0.0%,5,50.0%,
1.,,CSY-PB-ZM-AB-M-z11yahoo1z:Gandalf-Is-Coming-Get-Ready-for-Winter-Storms,10,0.5%,100.00%,20,0.5%,100.0%,1.00,605:12:39,20,0.5%,20,0.6%,40,0.4%,0,0.0%,5,50.0%
""".strip().decode('utf-8')

        report = parse_v2.OmnitureReport(csv_utils.convert_to_xls(csv_file))
        with self.assertRaisesMessage(exc.IncompleteReportException, 'Number of total sessions (20) is not equal to sum of session counts (10)'):
            # totals are too big (20) but entries are saved before this is checked so the test should pass
            report.parse()
        report.validate()

        self.assertTrue(all(entry.is_row_valid() for entry in report.entries.values()))

        self.assertEqual(datetime.date(2015, 9, 12), report.start_date)
        valid_entries = report.get_content_ad_stats()
        self.assertEqual(1, len(valid_entries))
        entry = valid_entries[0]

        self.assertEqual(10, entry.visits)
        self.assertEqual(40, entry.pageviews)
        self.assertEqual(1, entry.bounce_rate)
        self.assertEqual(20, entry.new_visits)
        self.assertEqual(10, entry.bounced_visits)
        self.assertEqual(0, entry.total_time_on_site)

        self.assertEqual(1, entry.content_ad_id)
        self.assertEqual('yahoo', entry.source_param)

        self.assertEqual('2015-09-12', entry.report_date)

        self.assertEqual({'Test Event': 5}, entry.goals)

    def test_validate_custom_coversion_goals(self):
        csv_file = """
######################################################################
# Company:,Zemanta
# URL:,.
# Site:,Global
# Range:,Sat. 12 Sep. 2015
# Report:,Tracking Code Report
# Description:,""
######################################################################
# Report Options:
# Report Type: ,"Ranked"
# Selected Metrics: ,"Visits, New Sessions, Unique Visitors, Bounce Rate, Pages/Session, Avg. Session Duration, Entries, Bounces, Page Views, Total Seconds Spent"
# Broken Down by: ,"None"
# Data Filter: ,"RANDOM"
# Compare to Report Suite: ,"None"
# Compare to Segment: ,"None"
# Item Filter: ,"None"
# Percent Shown as: ,"Number"
# Segment: ,"All Visits (No Segment)"
######################################################################
#
# Copyright 2015 Adobe Systems Incorporated. All rights reserved.
# Use of this document signifies your agreement to the Terms of Use (http://marketing.adobe.com/resources/help/terms.html?type=prod&locale=en_US) and Online Privacy Policy (http://my.omniture.com/x/privacy).
# Adobe Systems Incorporated products and services are licensed under the following Netratings patents: 5675510 5796952 6115680 6108637 6138155 6643696 and 6763386.
#
######################################################################

,Some other thing,,Visits,,New Sessions,Unique Visitors,,Bounce Rate,Pages/Session,Avg. Session Duration,Entries,,Bounces,,Page Views,,Total Seconds Spent,,Carts,Some unknown header,
1.,SOME_TOTALS,,20,0.5%,100.00%,20,0.5%,100.0%,1.00,605:12:39,20,0.5%,20,0.6%,40,0.4%,0,0.0%,5,50.0%,1,
1.,,CSY-PB-ZM-AB-M-z11yahoo1z:Gandalf-Is-Coming-Get-Ready-for-Winter-Storms,10,0.5%,100.00%,20,0.5%,100.0%,1.00,605:12:39,20,0.5%,20,0.6%,40,0.4%,0,0.0%,5,50.0%,1
""".strip().decode('utf-8')

        report = parse_v2.OmnitureReport(csv_utils.convert_to_xls(csv_file))
        with self.assertRaisesMessage(exc.IncompleteReportException, 'Number of total sessions (20) is not equal to sum of session counts (10)'):
            # totals are too big (20) but entries are saved before this is checked so the test should pass
            report.parse()
        report.validate()

        self.assertTrue(all(entry.is_row_valid() for entry in report.entries.values()))
        valid_entries = report.get_content_ad_stats()
        entry = valid_entries[0]
        self.assertTrue(all(entry.is_row_valid() for entry in report.entries.values()))

        self.assertEqual(10, entry.visits)
        self.assertEqual(40, entry.pageviews)
        self.assertEqual(1, entry.bounce_rate)
        self.assertEqual(20, entry.new_visits)
        self.assertEqual(10, entry.bounced_visits)
        self.assertEqual(0, entry.total_time_on_site)

        self.assertEqual(1, entry.content_ad_id)

        # all other unknown keys should be stripped away
        self.assertEqual({'Carts': 5}, entry.goals)

    def test_parse_bounce_rate(self):
        omniture_row_dict = {
            'Bounces': '123',
            'Unique Visits': '12',
            'Carts': '22',
            'Visits': '200',
            'Revenue': '31'
        }

        row = parse_v2.OmnitureReportRow(omniture_row_dict, datetime.date(2016, 1, 1), None, None, None, None)
        self.assertEquals(row.bounce_rate, 0.615)

        omniture_row_dict = {
            'Bounce Rate': '77%',
            'Bounces': '123',
            'Unique Visits': '12',
            'Carts': '22',
            'Visits': '200',
            'Revenue': '31'
        }

        row = parse_v2.OmnitureReportRow(omniture_row_dict, datetime.date(2016, 1, 1), None, None, None, None)
        self.assertEquals(row.bounce_rate, 0.77)

        omniture_row_dict = {
            'Bounce Rate': '0.78',
            'Bounces': '123',
            'Unique Visits': '12',
            'Carts': '22',
            'Visits': '200',
            'Revenue': '31'
        }

        row = parse_v2.OmnitureReportRow(omniture_row_dict, datetime.date(2016, 1, 1), None, None, None, None)
        self.assertEquals(row.bounce_rate, 0.78)
