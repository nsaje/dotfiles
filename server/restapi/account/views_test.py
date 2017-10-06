from restapi.views_test import RESTAPITest
from django.core.urlresolvers import reverse

import dash.models


class AccountsTest(RESTAPITest):

    @classmethod
    def account_repr(
        cls,
        id=1,
        agency_id=1,
        name='My test account',
        whitelist_publisher_groups=[153],
        blacklist_publisher_groups=[154],
    ):
        representation = {
            'id': str(id),
            'agencyId': str(agency_id) if agency_id else None,
            'name': name,
            'targeting': {
                'publisherGroups': {
                    'included': whitelist_publisher_groups,
                    'excluded': blacklist_publisher_groups,
                }
            },
        }
        return cls.normalize(representation)

    def validate_against_db(self, account):
        account_db = dash.models.Account.objects.get(pk=account['id'])
        settings_db = account_db.get_current_settings()
        expected = self.account_repr(
            id=account_db.id,
            agency_id=account_db.agency_id,
            name=settings_db.name,
            whitelist_publisher_groups=settings_db.whitelist_publisher_groups,
            blacklist_publisher_groups=settings_db.blacklist_publisher_groups,
        )
        self.assertEqual(expected, account)

    def test_accounts_list(self):
        r = self.client.get(reverse('accounts_list'))
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertGreater(len(resp_json['data']), 0)
        for item in resp_json['data']:
            self.validate_against_db(item)

    def test_accounts_post(self):
        new_account = self.account_repr(name='mytest',
                                        agency_id=1,
                                        whitelist_publisher_groups=[153, 154],
                                        blacklist_publisher_groups=[])
        del new_account['id']
        self._test_accounts_post(new_account)

    def test_accounts_post_no_agency(self):
        new_account = self.account_repr(name='mytest',
                                        agency_id=None,
                                        whitelist_publisher_groups=[153, 154],
                                        blacklist_publisher_groups=[])
        del new_account['id']
        self._test_accounts_post(new_account)

    def _test_accounts_post(self, new_account):
        r = self.client.post(
            reverse('accounts_list'),
            data=new_account, format='json')
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json['data'])
        new_account['id'] = resp_json['data']['id']
        self.assertEqual(resp_json['data'], new_account)

    def test_accounts_get(self):
        r = self.client.get(reverse('accounts_details', kwargs={'account_id': 186}))
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json['data'])

    def test_accounts_put(self):
        test_account = self.account_repr(id=186, whitelist_publisher_groups=[153, 154], blacklist_publisher_groups=[153, 154])
        r = self.client.put(
            reverse('accounts_details', kwargs={'account_id': 186}),
            data=test_account, format='json')
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json['data'])
        self.assertEqual(resp_json['data'], test_account)
