import datetime

from django.test import RequestFactory

from zemauth.models import User

from utils.test_case import TestCase
from utils import test_helper
from utils import exc

from dash import models
from dash.views import breakdowns_helpers


class CleanTestCase(TestCase):
    fixtures =['test_api.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=1)

    def test_clean_default_params(self):
        request = RequestFactory().get('/', {
            'start_date': '2016-01-01',
            'end_date': '2016-02-03',
            'filtered_sources': '1,3,4',
            'show_archived': 'true',
        })
        request.user = self.user

        params = breakdowns_helpers.clean_default_params(request)
        self.assertDictEqual(params, {
            'start_date': datetime.date(2016, 1, 1),
            'end_date': datetime.date(2016, 2, 3),
            'filtered_sources': test_helper.QuerySetMatcher(models.Source.objects.filter(pk__in=[1, 3, 4])),
            'show_archived': True,
        })

    def test_clean_page_params(self):
        request = RequestFactory().get('/', {
            'page': 1,
            'page_size': 10,
        })
        request.user = self.user

        page, page_size = breakdowns_helpers.clean_page_params(request)
        self.assertEqual(page, 1)
        self.assertEqual(page_size, 10)

    def test_clean_breakdown(self):

        breakdown = ['account', 'campaign', 'dma', 'day']
        self.assertEqual(breakdowns_helpers.clean_breakdown(None, None, breakdown), breakdown)

        breakdown = ['account', 'campaign', 'content_ad', 'dma', 'day']
        with self.assertRaises(exc.InvalidBreakdownError):
            breakdowns_helpers.clean_breakdown(None, None, breakdown)

    def test_clean_breakdown_page(self):
        breakdown = ['account', 'campaign', 'dma', 'day']
        request = RequestFactory().get('/', {
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
        })

        params = breakdowns_helpers.clean_breakdown_page(request, breakdown)
        self.assertItemsEqual(params, [
            {'account': 1, 'campaign': 6, 'dma': ['501', '502']},
            {'account': 1, 'campaign': 7, 'dma': ['501', '522']},
            {'account': 2, 'campaign': 33, 'dma': ['502']},
            {'account': 2, 'campaign': 2, 'dma': ['650', '677', '23']},
            {'account': 3, 'campaign': []},
        ])
