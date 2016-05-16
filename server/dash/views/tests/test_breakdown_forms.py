import datetime

from django.test import TestCase

from zemauth.models import User

from utils import test_helper

from dash import models
from dash.views import breakdown_forms


class CleanTestCase(TestCase):
    fixtures = ['test_api.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=1)

    def test_clean_default_params(self):
        request_data = {
            'start_date': '2016-01-01',
            'end_date': '2016-02-03',
            'filtered_sources': '1,3,4',
            'show_archived': 'true',
        }

        params = breakdown_forms.clean_default_params(self.user, request_data)

        self.assertDictEqual( params, {
            'date__gte': datetime.date(2016, 1, 1),
            'date__lte': datetime.date(2016, 2, 3),
            'source': test_helper.QuerySetMatcher(
                models.Source.objects.filter(pk__in=[1, 3, 4])),
            'show_archived': True,
        })

    def test_clean_page_params(self):
        request_data = {'page': 2, 'size': 15}

        page, page_size = breakdown_forms.clean_page_params(request_data)

        self.assertEqual(page, 2)
        self.assertEqual(page_size, 15)

        request_data = {}

        page, page_size = breakdown_forms.clean_page_params(request_data)

        self.assertEqual(page, breakdown_forms.DEFAULT_PAGE)
        self.assertEqual(page_size, breakdown_forms.DEFAULT_PAGE_SIZE)

    def test_clean_breakdown(self):

        self.assertEqual(
            ['account', 'campaign', 'dma', 'day'],
            breakdown_forms.clean_breakdown('/account/campaign/dma/day')
        )

        self.assertEqual(
            ['account', 'asd'],
            breakdown_forms.clean_breakdown('/account/asd/')
        )

    def test_clean_breakdown_page(self):
        breakdown = ['account', 'campaign', 'dma', 'day']
        request_data = {
            'breakdown_page': """{
                "1": {
                    "6": ["501","502"],
                    "7": ["501","522"]
                },
                "2": {
                    "33": ["502"],
                    "2": ["650","677","23"]
                },
                "3": []
            }""",
            'campaign': '6,7',
            'dma': '501,533,454,456',
            'start_date': '2016-02-02',
            'end_date': '2016-02-02',
            'content_ad_id': 123,
        }

        breakdown_page = breakdown_forms.clean_breakdown_page(request_data, breakdown)
        self.assertItemsEqual(breakdown_page, [
            {'account': 1,
             'campaign': 6,
             'dma': ['501', '502']},
            {'account': 1,
             'campaign': 7,
             'dma': ['501', '522']},
            {'account': 2,
             'campaign': 33,
             'dma': ['502']},
            {'account': 2,
             'campaign': 2,
             'dma': ['650', '677', '23']},
            {'account': 3,
             'campaign': []},
        ])

        request_data = {}
        breakdown_page = breakdown_forms.clean_breakdown_page(request_data, breakdown)
        self.assertEquals(breakdown_page, None)
