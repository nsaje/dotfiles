import csv
import logging

from django.db import transaction

from utils.command_helpers import ExceptionCommand
import dash.regions
from dash import constants
from dash import models

import geolocation

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

    help = "Import/update MaxMind locations into Eins"

    def add_arguments(self, parser):
        parser.add_argument('maxmind_csv', type=str, help='example filename: GeoIP2-City-Locations-en.csv')

    def handle(self, *args, **options):
        maxmind_csv_path = options['maxmind_csv']
        locations_by_type = self.get_locations(maxmind_csv_path)

        objs = []
        for loc_type, location in locations_by_type.iteritems():
            for key, name in location.iteritems():
                objs.append(geolocation.Geolocation(type=loc_type, key=key, name=name))

        with transaction.atomic():
            geolocation.Geolocation.objects.all().delete()
            geolocation.Geolocation.objects.bulk_create(objs)

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
