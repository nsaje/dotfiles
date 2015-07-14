from django import test


class SupplyReportEmailTestCase(test.TestCase):
    fixtures = ['test_reports_base.yaml', 'test_article_stats.yaml']

    def setUp(self):
        refresh.refresh_adgroup_stats()
