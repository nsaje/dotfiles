from mock import patch, Mock

from django import test
from django import http
import xlrd

from dash import views


@patch('dash.views.models')
@patch('dash.views.api')
@patch('dash.views.get_ad_group')
class AdGroupAdsExportTestCase(test.TestCase):
    def test_get_csv(self, mock_get_ad_group, mock_api, mock_models):
        ad_group_id = 1

        mock_ad_group = Mock()
        mock_ad_group.id = ad_group_id
        mock_get_ad_group.return_value = mock_ad_group

        mock_network = Mock()
        mock_network.id = 1
        mock_network.name = 'Test Network'
        mock_models.Network.objects.all.return_value = [mock_network]

        mock_article = Mock()
        mock_article.id = 1
        mock_article.title = 'Test Article'
        mock_models.Article.objects.all.return_value = [mock_article]

        request = http.HttpRequest()
        request.GET['type'] = 'csv'
        request.GET['start_date'] = '2014-06-25'
        request.GET['end_date'] = '2014-07-02'
        request.user = Mock()

        mock_api.query.return_value = [{
            'article': 1,
            'network': 1,
            'date': '2014-07-01',
            'cost': 1000,
            'cpc': 10,
            'clicks': 103,
            'impressions': 100000,
            'ctr': 1.03
        }]

        response = views.AdGroupAdsExport().get(request, ad_group_id)

        expected_content = '''"Article","Network","Date","Cost","CPC","Clicks","Impressions","CTR"
"Test Article","Test Network","2014-07-01",1000,10,103,100000,1.03
'''

        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename=networks_report_2014-06-25_2014-07-02.csv'
        )
        self.assertEqual(response.content, expected_content)

    def test_get_excel(self, mock_get_ad_group, mock_api, mock_models):
        ad_group_id = 1

        mock_ad_group = Mock()
        mock_ad_group.id = ad_group_id
        mock_get_ad_group.return_value = mock_ad_group

        mock_network = Mock()
        mock_network.id = 1
        mock_network.name = 'Test Network'
        mock_models.Network.objects.all.return_value = [mock_network]

        mock_article = Mock()
        mock_article.id = 1
        mock_article.title = 'Test Article'
        mock_models.Article.objects.all.return_value = [mock_article]

        request = http.HttpRequest()
        request.GET['type'] = 'excel'
        request.GET['start_date'] = '2014-06-25'
        request.GET['end_date'] = '2014-07-02'
        request.user = Mock()

        mock_api.query.return_value = [{
            'article': 1,
            'network': 1,
            'date': '2014-07-01',
            'cost': 1000,
            'cpc': 10,
            'clicks': 103,
            'impressions': 100000,
            'ctr': 1.03
        }]

        response = views.AdGroupAdsExport().get(request, ad_group_id)

        self.assertEqual(response['Content-Type'], 'application/octet-stream')
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename=networks_report_2014-06-25_2014-07-02.xlsx'
        )

        workbook = xlrd.open_workbook(file_contents=response.content)
        self.assertIsNotNone(workbook)

        worksheet = workbook.sheet_by_name('Networks Report')
        self.assertIsNotNone(worksheet)

        self.assertEqual(worksheet.cell_value(0, 0), 'Article')
        self.assertEqual(worksheet.cell_value(0, 1), 'Network')
        self.assertEqual(worksheet.cell_value(0, 2), 'Date')
        self.assertEqual(worksheet.cell_value(0, 3), 'Cost')
        self.assertEqual(worksheet.cell_value(0, 4), 'CPC')
        self.assertEqual(worksheet.cell_value(0, 5), 'Clicks')
        self.assertEqual(worksheet.cell_value(0, 6), 'Impressions')
        self.assertEqual(worksheet.cell_value(0, 7), 'CTR')

        self.assertEqual(worksheet.cell_value(1, 0), 'Test Article')
        self.assertEqual(worksheet.cell_value(1, 1), 'Test Network')
        self.assertEqual(worksheet.cell_value(1, 2), '2014-07-01')
        self.assertEqual(worksheet.cell_value(1, 3), 1000)
        self.assertEqual(worksheet.cell_value(1, 4), 10)
        self.assertEqual(worksheet.cell_value(1, 5), 103)
        self.assertEqual(worksheet.cell_value(1, 6), 100000)
        self.assertEqual(worksheet.cell_value(1, 7), 0.0103)
