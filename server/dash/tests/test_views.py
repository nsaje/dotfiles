from mock import patch, Mock
import datetime

from django import test
from django import http
import xlrd

from dash import views


class AdGroupAdsExportTestCase(test.TestCase):
    def setUp(self):
        self.get_ad_group_patcher = patch('dash.views.get_ad_group')
        self.api_patcher = patch('dash.views.api')
        self.models_patcher = patch('dash.views.models')

        self.mock_get_ad_group = self.get_ad_group_patcher.start()
        self.mock_api = self.api_patcher.start()
        self.mock_models = self.models_patcher.start()

        self.ad_group_id = 1

        self.mock_ad_group = Mock()
        self.mock_ad_group.id = self.ad_group_id
        self.mock_get_ad_group.return_value = self.mock_ad_group

        self.mock_network1 = Mock()
        self.mock_network1.id = 1
        self.mock_network1.name = 'Test Network 1'

        self.mock_network2 = Mock()
        self.mock_network2.id = 2
        self.mock_network2.name = 'Test Network 2'

        self.mock_models.Network.objects.all.return_value = [self.mock_network1, self.mock_network2]

        self.mock_article = Mock()
        self.mock_article.id = 1
        self.mock_article.title = 'Test Article'
        self.mock_models.Article.objects.filter.return_value = [self.mock_article]

        self.mock_api.query.return_value = [{
            'article': 1,
            'network': 1,
            'date': datetime.date(2014, 7, 1),
            'cost': 1000,
            'cpc': 10,
            'clicks': 103,
            'impressions': 100000,
            'ctr': 1.031231231
        }]

    def tearDown(self):
        self.get_ad_group_patcher.stop()
        self.api_patcher.stop()
        self.models_patcher.stop()

    def test_get_csv(self):
        request = http.HttpRequest()
        request.GET['type'] = 'csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.user = Mock()

        response = views.AdGroupAdsExport().get(request, self.ad_group_id)

        expected_content = '''"Date","Article","Network","Cost","CPC","Clicks","Impressions","CTR"
"2014-06-30","Test Article","Test Network 1",0,0,0,0,0
"2014-06-30","Test Article","Test Network 2",0,0,0,0,0
"2014-07-01","Test Article","Test Network 1",1000,10,103,100000,1.031231231
"2014-07-01","Test Article","Test Network 2",0,0,0,0,0
'''

        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename=networks_report_2014-06-30_2014-07-01.csv'
        )
        self.assertEqual(response.content, expected_content)

    def test_get_excel(self):
        request = http.HttpRequest()
        request.GET['type'] = 'excel'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.user = Mock()

        response = views.AdGroupAdsExport().get(request, self.ad_group_id)

        self.assertEqual(response['Content-Type'], 'application/octet-stream')
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename=networks_report_2014-06-30_2014-07-01.xlsx'
        )

        workbook = xlrd.open_workbook(file_contents=response.content)
        self.assertIsNotNone(workbook)

        worksheet = workbook.sheet_by_name('Networks Report')
        self.assertIsNotNone(worksheet)

        self.assertEqual(worksheet.cell_value(0, 0), 'Date')
        self.assertEqual(worksheet.cell_value(0, 1), 'Article')
        self.assertEqual(worksheet.cell_value(0, 2), 'Network')
        self.assertEqual(worksheet.cell_value(0, 3), 'Cost')
        self.assertEqual(worksheet.cell_value(0, 4), 'CPC')
        self.assertEqual(worksheet.cell_value(0, 5), 'Clicks')
        self.assertEqual(worksheet.cell_value(0, 6), 'Impressions')
        self.assertEqual(worksheet.cell_value(0, 7), 'CTR')

        self.assertEqual(worksheet.cell_value(1, 0), 41820.0)
        self.assertEqual(worksheet.cell_value(1, 1), 'Test Article')
        self.assertEqual(worksheet.cell_value(1, 2), 'Test Network 1')
        self.assertEqual(worksheet.cell_value(1, 3), 0)
        self.assertEqual(worksheet.cell_value(1, 4), 0)
        self.assertEqual(worksheet.cell_value(1, 5), 0)
        self.assertEqual(worksheet.cell_value(1, 6), 0)
        self.assertEqual(worksheet.cell_value(1, 7), 0)

        self.assertEqual(worksheet.cell_value(2, 0), 41820.0)
        self.assertEqual(worksheet.cell_value(2, 1), 'Test Article')
        self.assertEqual(worksheet.cell_value(2, 2), 'Test Network 2')
        self.assertEqual(worksheet.cell_value(2, 3), 0)
        self.assertEqual(worksheet.cell_value(2, 4), 0)
        self.assertEqual(worksheet.cell_value(2, 5), 0)
        self.assertEqual(worksheet.cell_value(2, 6), 0)
        self.assertEqual(worksheet.cell_value(2, 7), 0)

        self.assertEqual(worksheet.cell_value(3, 0), 41821.0)
        self.assertEqual(worksheet.cell_value(3, 1), 'Test Article')
        self.assertEqual(worksheet.cell_value(3, 2), 'Test Network 1')
        self.assertEqual(worksheet.cell_value(3, 3), 1000)
        self.assertEqual(worksheet.cell_value(3, 4), 10)
        self.assertEqual(worksheet.cell_value(3, 5), 103)
        self.assertEqual(worksheet.cell_value(3, 6), 100000)
        self.assertEqual(worksheet.cell_value(3, 7), 0.01031231231)

        self.assertEqual(worksheet.cell_value(4, 0), 41821.0)
        self.assertEqual(worksheet.cell_value(4, 1), 'Test Article')
        self.assertEqual(worksheet.cell_value(4, 2), 'Test Network 2')
        self.assertEqual(worksheet.cell_value(4, 3), 0)
        self.assertEqual(worksheet.cell_value(4, 4), 0)
        self.assertEqual(worksheet.cell_value(4, 5), 0)
        self.assertEqual(worksheet.cell_value(4, 6), 0)
        self.assertEqual(worksheet.cell_value(4, 7), 0)
