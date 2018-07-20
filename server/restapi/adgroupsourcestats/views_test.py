import decimal
import mock

from django.contrib.auth.models import Permission
from django.core.urlresolvers import reverse

from restapi.common.views_base_test import RESTAPITest

import core.source
import core.entity.adgroup
from zemauth.models import User
from utils.magic_mixer import magic_mixer


class RealtimestatsViewsTest(RESTAPITest):
    @mock.patch("dash.features.realtimestats.get_ad_group_sources_stats")
    def test_adgroup_sources_realtimestats(self, mock_get):
        permission = Permission.objects.get(codename="can_use_restapi")
        user = User.objects.get(pk=1)
        user.user_permissions.remove(permission)

        sources = magic_mixer.cycle(2).blend(core.source.Source, bidder_slug=magic_mixer.RANDOM)
        data = [
            {"source": sources[0], "spend": decimal.Decimal("12.34567")},
            {"source": sources[1], "spend": decimal.Decimal("0.11111")},
        ]

        mock_get.return_value = data
        r = self.client.get(reverse("adgroups_realtimestats_sources", kwargs={"ad_group_id": 2040}))

        resp_json = self.assertResponseValid(r, data_type=list)

        expected = [{"source": sources[0].name, "spend": "12.35"}, {"source": sources[1].name, "spend": "0.11"}]
        self.assertEqual(resp_json["data"], expected)

        mock_get.assert_called_with(core.entity.adgroup.AdGroup.objects.get(pk=2040), use_local_currency=True)
