import csv
import logging

import unicodecsv
from django.db import transaction

from utils.command_helpers import ExceptionCommand
import dash.regions
from dash import constants

import dash.geolocation

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

    help = "Import/update MaxMind locations into Eins"

    def add_arguments(self, parser):
        parser.add_argument('maxmind_csv', type=str, help='example filename: GeoIP2-City-Locations-en.csv')
        parser.add_argument('yahoo_mapping_csv', type=str, help='example filename: yahoo-mapping.csv')
        parser.add_argument('outbrain_mapping_csv', type=str, help='example filename: outbrain-mapping.csv')

    def handle(self, *args, **options):
        locations_by_type = self.get_locations(options['maxmind_csv'])
        yahoo_mapping = self.get_mapping(options['yahoo_mapping_csv'], 'woeid')
        outbrain_mapping = self.get_mapping(options['outbrain_mapping_csv'], 'outbrain_id')

        objs = []
        for loc_type, location in locations_by_type.iteritems():
            for key, name in location.iteritems():
                objs.append(dash.geolocation.Geolocation(
                    type=loc_type,
                    key=key,
                    name=name,
                    woeid=yahoo_mapping.get(key, ''),
                    outbrain_id=outbrain_mapping.get(key, ''),
                ))

        # add ZIP code mappings
        for key in set(self.get_zips(yahoo_mapping)).union(set(self.get_zips(outbrain_mapping))):
            objs.append(dash.geolocation.Geolocation(
                type=constants.LocationType.ZIP,
                key=key,
                name=key,
                woeid=yahoo_mapping.get(key, ''),
                outbrain_id=outbrain_mapping.get(key, ''),
            ))

        with transaction.atomic():
            dash.geolocation.Geolocation.objects.all().delete()
            dash.geolocation.Geolocation.objects.bulk_create(objs)

    @staticmethod
    def get_locations(maxmind_csv_path):
        countries = {}
        regions = {}
        dmas = dash.regions.DMA_BY_CODE  # use our hardcoded DMA definitions because MaxMind DB doesn't have names
        cities = {}

        with open(maxmind_csv_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            for row in reader:
                if row['country_name']:
                    countries[row['country_iso_code']] = row['country_name']

                if row['subdivision_1_name']:
                    name_tokens = [row['subdivision_1_name']]
                    if row['country_name']:
                        name_tokens.append(row['country_name'])
                    region_key = '{}-{}'.format(row['country_iso_code'], row['subdivision_1_iso_code'])
                    regions[region_key] = ', '.join(name_tokens)

                if row['city_name']:
                    name_tokens = [row['city_name']]
                    if row['subdivision_2_name']:
                        name_tokens.append(row['subdivision_2_name'])
                    if row['subdivision_1_name']:
                        name_tokens.append(row['subdivision_1_name'])
                    if row['country_name']:
                        name_tokens.append(row['country_name'])
                    full_name = ', '.join(name_tokens) + ' [%s]' % row['geoname_id']
                    cities[row['geoname_id']] = full_name

        return {
            constants.LocationType.COUNTRY: countries,
            constants.LocationType.REGION: regions,
            constants.LocationType.DMA: dmas,
            constants.LocationType.CITY: cities,
        }

    @staticmethod
    def get_mapping(csv_path, column_name):
        mapping = {}
        with open(csv_path, 'r') as csvfile:
            reader = unicodecsv.DictReader(csvfile, delimiter=',', quotechar='"')
            for row in reader:
                mapping[row['key']] = row[column_name]
        return mapping

    @staticmethod
    def get_zips(mapping):
        for key in mapping.keys():
            if len(key) > 2 and key[2] == ':':
                yield key
