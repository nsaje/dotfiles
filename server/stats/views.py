from django.core.exceptions import ValidationError

# Create your views here.
from stats import mock_data
from utils import api_common
from utils import exc
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


#
# http://localhost:8000/api/experimental/stats/testdata/?breakdown=ad_group,age,date&ranges=1|3,1|4,1|5&level=0
#
# breakdown - comma separated values
# ranges - comma separated ranges - range = from|to ~ [from, to)
# level - breakdown level to return
#
class TestData(api_common.BaseApiView):
    def get(self, request):
        if not request.user.has_perm('zemauth.can_access_table_breakdowns_development_features'):
            raise exc.MissingDataError()

        breakdown_list = request.GET.get('breakdowns').split(',')
        breakdown_range_list = request.GET.get('ranges').split(',')
        level = int(request.GET.get('level', '0'))

        if len(breakdown_list) != len(breakdown_range_list):
            raise ValidationError('')

        breakdowns = []

        for breakdown, breakdown_range in zip(breakdown_list, breakdown_range_list):
            range_array = [int(s) for s in breakdown_range.split('|')]
            range_array.append(range_array[0] + 1) if len(range_array) == 1 else None
            breakdowns.append({'name': breakdown, 'range': range_array})

        data = mock_data.generate_random_breakdowns(breakdowns, level)

        return self.create_api_response(data)
