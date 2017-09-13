import json

from django.core.urlresolvers import reverse

import core.entity
from core.publisher_groups import publisher_group_helpers
import restapi.views_test
from utils.magic_mixer import magic_mixer


class PublisherBlacklistTest(restapi.views_test.RESTAPITest):

    def setUp(self):
        super(PublisherBlacklistTest, self).setUp()
        self.test_request = magic_mixer.blend_request_user()
        self.test_ad_group = magic_mixer.blend(core.entity.AdGroup, campaign_id=608)

    def _get_resp_json(self, ad_group_id):
        r = self.client.get(reverse('publishers_list', kwargs={'ad_group_id': ad_group_id}))
        resp_json = json.loads(r.content)
        return resp_json

    def test_adgroups_publishers_list(self):
        publisher_group_helpers.blacklist_publishers(self.test_request, [{'publisher': 'cnn.com', 'source': None, 'include_subdomains': True}], self.test_ad_group)

        r = self.client.get(reverse('publishers_list', kwargs={'ad_group_id': self.test_ad_group.id}))

        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertEqual(
            resp_json['data'],
            [{
                'name': 'cnn.com',
                'source': None,
                'status': 'BLACKLISTED',
                'level': 'ADGROUP',
            }]
        )

    def test_adgroups_publishers_put(self):
        test_blacklist = [{
            'name': 'cnn2.com',
            'source': 'gumgum',
            'status': 'BLACKLISTED',
            'level': 'ADGROUP',
        }]
        r = self.client.put(
            reverse('publishers_list', kwargs={'ad_group_id': self.test_ad_group.id}),
            data=test_blacklist, format='json')
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(resp_json['data'], test_blacklist)

        self.assertEqual(
            self._get_resp_json(self.test_ad_group.id)['data'],
            [{
                'name': 'cnn2.com',
                'source': 'gumgum',
                'status': 'BLACKLISTED',
                'level': 'ADGROUP',
            }]
        )

    def test_adgroups_publishers_put_unlist(self):
        source = core.source.Source.objects.get(bidder_slug='gumgum')
        publisher_group_helpers.blacklist_publishers(self.test_request, [{'publisher': 'cnn.com', 'source': source, 'include_subdomains': True}], self.test_ad_group)

        put_data = [{
            'name': 'cnn.com',
            'source': 'gumgum',
            'status': 'ENABLED',
            'level': 'ADGROUP',
        }]
        r = self.client.put(
            reverse('publishers_list', kwargs={'ad_group_id': self.test_ad_group.id}),
            data=put_data, format='json')
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(resp_json['data'], put_data)

        self.assertEqual(
            self._get_resp_json(self.test_ad_group.id)['data'],
            []
        )
