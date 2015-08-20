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

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('-f', '--filename', help='file', dest='filename'),
    )

    def handle(self, *args, **options):

        print("WARNING: This script will potentially delete data from content ad stats tables!")

        try:
            filename = options['filename']
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
                    csvreport = parse_v2.CsvReport(f.read())
                    # parse will throw exceptions in case of errors
                    csvreport.parse()
                    logger.info(csvreport.debug_parsing_overview())
                    # serialize report
                    # api_contentads.process_report(csvreport.entries, constants.ReportType.GOOGLE_ANALYTICS)
                except:
                    traceback.print_exc()
                    logger.exception("Failed processing file {}".format(filename))
        except:
           logger.exception('Failed opening file')
