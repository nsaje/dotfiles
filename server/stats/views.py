from django.core.exceptions import ValidationError
from django.shortcuts import render

# Create your views here.
from stats import mock_data
from utils import api_common
from dash.views import helpers
from random import random
from datetime import datetime
from datetime import timedelta

TEST_COLUMNS = 10
TEST_COLUMNS_TYPES = ['int', 'string', 'string', 'string']
TEST_BREAKDOWNS = ['date', 'age', 'ad_group']

TEST_BREAKDOWNS_DATES = [(datetime(2016, 4, 1) + timedelta(days=i)).strftime('%b %d %Y') for i in range(30)]
TEST_BREAKDOWNS_AD_GROUPS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
TEST_BREAKDOWNS_AGES = ['<18', '18-21', '21-30', '30-40', '30-40', '40-50', '50-60', '60-70', '70-80', '80-90', '99+']
TEST_BREAKDOWNS_SEX = ['man', 'woman']



class TestMetaData(api_common.BaseApiView):
    pass


# http://localhost:8000/api/experimental/stats/testdata/?level-1=ad_group&level-2=date&level-3=age&level-1-pagination=0|5&level-2-pagination=0|5&level-3-pagination=0|5
class TestData(api_common.BaseApiView):
    def get(self, request):
        # level=from|to|[all]

        breakdown_list = request.GET.get('breakdowns').split(',')
        range_list = request.GET.get('ranges').split(',')

        if len(breakdown_list) != len(range_list):
            raise ValidationError('')

        breakdowns = []

        for breakdown, range in zip(breakdown_list, range_list):
            range_array = [int(s) for s in range.split('|')]
            breakdowns.append({'name': breakdown, 'range': range_array})

        data = mock_data.generate_random_data(breakdowns)
        return self.create_api_response(data)

