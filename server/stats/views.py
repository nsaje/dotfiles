from django.shortcuts import render

# Create your views here.
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

        l1 = request.GET.get('level-1')
        l2 = request.GET.get('level-2')
        l3 = request.GET.get('level-3')

        l1_p = [int(i) for i in request.GET.get('level-1-pagination').split('|')] if l1 else None
        l2_p = [int(i) for i in request.GET.get('level-2-pagination').split('|')] if l2 else None
        l3_p = [int(i) for i in request.GET.get('level-3-pagination').split('|')] if l3 else None

        data = self.get_test_data(l1, l2, l3, l1_p, l2_p, l3_p)
        return self.create_api_response(data)


    def get_test_data(self, l1, l2, l3, l1_p, l2_p, l3_p):
        # stats
        #   -> data ~ totals
        #   -> breakdown (level-1)
        #       -> pagination
        #       -> rows []
        #           -> data ~ totals
        #           -> breakdown (level-2)
        #               -> pagination
        #               -> rows []
        #                   -> data ~ totals
        #                   -> breakdown (level-2)
        #                       -> pagination
        #                       -> rows []
        #                       -> ...
        stats = {}
        stats['data'] = ['Total'] + [str(random()*1000000) for _ in range(TEST_COLUMNS)]

        # Breakdown 1
        data_l1, pagination_l1 = self.get_test_data_breakdown(l1, l1_p)
        breakdown_l1 = {}
        rows_l1 = []
        breakdown_l1['rows'] = rows_l1
        breakdown_l1['pagination'] = pagination_l1
        stats['breakdown'] = breakdown_l1

        for d_l1 in data_l1:
            row = {}
            rows_l1.append(row)
            row['data'] = self.get_random_data(l1, d_l1)


            # Breakdown 2
            if not l2:
                continue
            data_l2, pagination_l2 = self.get_test_data_breakdown(l2, l2_p)
            breakdown_l2 = {}
            rows_l2 = []
            breakdown_l2['rows'] = rows_l2
            breakdown_l2['pagination'] = pagination_l2
            row['breakdown'] = breakdown_l2

            for d_l2 in data_l2:
                row = {}
                rows_l2.append(row)
                row['data'] = self.get_random_data(l2, d_l2)

                # Breakdown 3
                if not l3:
                    continue
                data_l3, pagination_l3 = self.get_test_data_breakdown(l3, l3_p)
                breakdown_l3 = {}
                rows_l3 = []
                breakdown_l3['rows'] = rows_l3
                breakdown_l3['pagination'] = pagination_l3
                row['breakdown'] = breakdown_l3

                for d_l3 in data_l3:
                    row = {}
                    rows_l3.append(row)
                    row['data'] = self.get_random_data(l3, d_l3)

        return stats

    def get_random_data (self, level, data):
        return ([data] + [('%.2f' % (random()*10000)) for _ in range(TEST_COLUMNS)])


    def get_test_data_breakdown(self, l, l_p):
        data = None
        if l == 'date':
            data = TEST_BREAKDOWNS_DATES
        elif l == 'age':
            data = TEST_BREAKDOWNS_AGES
        elif l == 'ad_group':
            data = TEST_BREAKDOWNS_AD_GROUPS
        elif l == 'sex':
            data = TEST_BREAKDOWNS_SEX

        data_size = len(data)
        data_from = l_p[0]
        data_to = min(l_p[1], data_size)

        if data_from >= data_to or data_from < 0:
            raise Exception('Out of bounds')

        pagination = {
            'from': data_from,
            'to': data_to,
            'count': data_size
        }
        partial_data = data[data_from:data_to]

        return partial_data, pagination




