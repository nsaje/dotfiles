"""
Script for processing or reprocessing reports

WARNING: This will delete records in the DB tables
"""
import sys
import logging
import traceback

from convapi import parse_v2
from reports import api_contentads
from reports import constants
from django.core.management.base import BaseCommand
from optparse import make_option
from utils.csv_utils import convert_to_xls

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('-f', '--filename', help='file', dest='filename'),
        make_option('-t', '--report_type', help='Report type - omniture or ga', dest='report_type'),
    )

    def handle(self, *args, **options):

        print("WARNING: This script will potentially delete data from content ad stats tables!")

        try:
            filename = options['filename']
            report_type = options['report_type']
        except:
            logger.exception("Failed parsing command line arguments")
            sys.exit(1)

        if filename == '' or filename is None:
            print("Invalid filename")
            sys.exit(1)

        try:
            with open(filename) as f:
                print("Processing file {}".format(filename))
                try:
                    content = f.read()

                    magic_string = '\xef\xbb\xbf'
                    start_of_content = content[:3]
                    if start_of_content == magic_string:
                        content = content[len(magic_string):]

                    if report_type == 'ga':
                        report = parse_v2.GAReport(content)
                    elif report_type == 'omniture':
                        if filename.endswith('.csv'):
                            content = convert_to_xls(content)
                        report = parse_v2.OmnitureReport(content)
                    else:
                        raise Exception('Unknown report type {}'.format(report_type))

                    # parse will throw exceptions in case of errors
                    report.parse()
                    report.validate()
                    # serialize report
                    # api_contentads.process_report(csvreport.entries, constants.ReportType.GOOGLE_ANALYTICS)
                except:
                    traceback.print_exc()
                    logger.exception("Failed processing file {}".format(filename))
        except:
           logger.exception('Failed opening file')
