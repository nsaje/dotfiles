import mock

from django.contrib.auth.models import Permission
from django.core.urlresolvers import reverse

from restapi.views_test import RESTAPITest

from dash import models
from dash.features import realtimestats
from zemauth.models import User


class RealtimestatsViewsTest(RESTAPITest):

    @mock.patch('dash.features.realtimestats.service.get_ad_group_stats')
    def test_adgroups_realtimestats(self, mock_get):
        realtimestats.views.REALTIME_STATS_AGENCIES.append(1)

        mock_get.return_value = {'clicks': 12321, 'spend': 12.3}
        r = self.client.get(reverse('adgroups_realtimestats', kwargs={'ad_group_id': 2040}))

        resp_json = self.assertResponseValid(r)
        self.assertEqual(resp_json['data'], {'spend': '12.30', 'clicks': 12321})

        mock_get.assert_called_with(models.AdGroup.objects.get(pk=2040))

        realtimestats.views.REALTIME_STATS_AGENCIES.remove(1)

    def test_adgroups_realtimestats_unauthorized(self):
        r = self.client.get(reverse('adgroups_realtimestats', kwargs={'ad_group_id': 2040}))
        self.assertEqual(r.status_code, 404)

    @mock.patch('dash.features.realtimestats.service.get_ad_group_sources_stats')
    def test_adgroup_sources_realtimestats(self, mock_get):
        permission = Permission.objects.get(codename='can_use_restapi')
        user = User.objects.get(pk=1)
        user.user_permissions.remove(permission)

        data = [{'source': 's1', 'spend': 12.3}, {'source': 's2', 'spend': 0.1}]

        mock_get.return_value = data
        r = self.client.get(reverse('adgroups_realtimestats_sources', kwargs={'ad_group_id': 2040}))

        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(resp_json['data'], data)

        mock_get.assert_called_with(models.AdGroup.objects.get(pk=2040))
