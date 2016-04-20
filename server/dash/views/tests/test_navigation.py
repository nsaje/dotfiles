# -*- coding: utf-8 -*-
import json
from mock import patch
import datetime

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import Permission

from utils import test_helper

from zemauth.models import User


class MockDatetime(datetime.datetime):

    @classmethod
    def utcnow(cls):
        return datetime.datetime(2016, 1, 2)


class NavigationAllAccountsDataViewTest(TestCase):
    fixtures = ['test_navigation.yaml']

    def _get(self, user_id, filtered_sources=None):
        username = User.objects.get(pk=user_id).email
        self.client.login(username=username, password='secret')

        response = self.client.get(reverse('navigation_all_accounts'),
                                   data={'filtered_sources': filtered_sources})

        response = json.loads(response.content)
        return response['data']

    def test_get(self):
        response = self._get(1)
        self.assertDictEqual(response, {
            'accounts_count': 1,
            'default_account_id': 1
        })

        response = self._get(2)
        self.assertDictEqual(response, {
            'accounts_count': 1,
            'default_account_id': 2
        })

    def test_get_no_accounts(self):
        response = self._get(4)
        self.assertDictEqual(response, {
            'accounts_count': 0
        })

    def test_get_many_accounts(self):
        response = self._get(5)
        self.assertDictEqual(response, {
            'accounts_count': 3,
            'default_account_id': 2
        })

    def test_get_filtered_sources(self):
        response = self._get(1, [3])
        self.assertDictEqual(response, {
            'accounts_count': 0
        })

        # has no filter_sources permission
        response = self._get(2, [3])
        self.assertDictEqual(response, {
            'accounts_count': 1,
            'default_account_id': 2
        })


class NavigationDataViewTest(TestCase):
    fixtures = ['test_navigation.yaml']

    def _get(self, user_id, level, obj_id, filtered_sources=None):

        username = User.objects.get(pk=user_id).email
        self.client.login(username=username, password='secret')

        response = self.client.get(reverse('navigation', kwargs={
            'level_': level,
            'id_': obj_id,
        }), data={
            'filtered_sources': filtered_sources
        })

        response = json.loads(response.content)
        return response['data']

    def test_get_account(self):
        response = self._get(1, 'accounts', 1)

        self.assertDictEqual(response, {
            'account': {
                'archived': False,
                'id': 1,
                'name': 'test account 1',
            }
        })

        # archived entity
        response = self._get(3, 'accounts', 3)

        self.assertDictEqual(response, {
            'account': {
                'archived': True,
                'id': 3,
                'name': 'test account 3',
            }
        })

    def test_get_account_without_archived_flag(self):
        response = self._get(2, 'accounts', 2)

        self.assertDictEqual(response, {
            'account': {
                'id': 2,
                'name': 'test account 2',
            }
        })

    def test_get_account_no_access(self):
        # has other accounts available
        response = self._get(1, 'accounts', 2)
        self.assertDictEqual(response, {
            'message': 'Account does not exist',
            'error_code': 'MissingDataError'
        })

        # has no accounts available
        response = self._get(4, 'accounts', 2)
        self.assertDictEqual(response, {
            'message': 'Account does not exist',
            'error_code': 'MissingDataError'
        })

    def test_get_campaign(self):
        response = self._get(1, 'campaigns', 1)

        self.assertDictEqual(response, {
            'account': {
                'archived': False,
                'id': 1,
                'name': 'test account 1',
            },
            'campaign': {
                'archived': False,
                'id': 1,
                'name': 'test campaign 1',
                'landingMode': False,
            }
        })

        # archived entity
        response = self._get(3, 'campaigns', 3)

        self.assertDictEqual(response, {
            'account': {
                'archived': True,
                'id': 3,
                'name': 'test account 3',
            },
            'campaign': {
                'archived': True,
                'id': 3,
                'name': 'test campaign 3',
                'landingMode': False,
            }
        })

    def test_get_campaign_without_archived_flag(self):
        response = self._get(2, 'campaigns', 2)

        self.assertDictEqual(response, {
            'account': {
                'id': 2,
                'name': 'test account 2',
            },
            'campaign': {
                'id': 2,
                'name': 'test campaign 2',
                'landingMode': False,
            }
        })

    def test_get_campaign_no_access(self):
        # has other campaigns available
        response = self._get(1, 'campaigns', 2)
        self.assertDictEqual(response, {
            'message': 'Campaign does not exist',
            'error_code': 'MissingDataError'
        })

        # has no campaigns available
        response = self._get(4, 'campaigns', 2)
        self.assertDictEqual(response, {
            'message': 'Campaign does not exist',
            'error_code': 'MissingDataError'
        })

    @patch('datetime.datetime', MockDatetime)
    def test_get_ad_group(self):
        response = self._get(1, 'ad_groups', 1)

        self.assertDictEqual(response, {
            'account': {
                'archived': False,
                'id': 1,
                'name': 'test account 1',
            },
            'campaign': {
                'archived': False,
                'id': 1,
                'name': 'test campaign 1',
                'landingMode': False,
            },
            'ad_group': {
                'archived': False,
                'id': 1,
                'name': 'test adgroup 1',
                'state': 1,
                'status': 1,
                'autopilot_state': 2,
                'active': 'active',
            }
        })

        # archived entity
        user = User.objects.get(pk=2)
        permission = Permission.objects.get(codename='view_archived_entities')
        user.user_permissions.add(permission)

        response = self._get(2, 'ad_groups', 4)

        self.assertDictEqual(response, {
            'account': {
                'archived': False,
                'id': 2,
                'name': 'test account 2',
            },
            'campaign': {
                'archived': False,
                'id': 2,
                'name': 'test campaign 2',
                'landingMode': False,
            },
            'ad_group': {
                'archived': True,
                'id': 4,
                'name': 'test adgroup 4',
                'state': 2,
                'status': 2,
                'autopilot_state': 2,
                'active': 'stopped',
            }
        })

    @patch('datetime.datetime', MockDatetime)
    def test_get_ad_group_without_archived_flag(self):
        response = self._get(2, 'ad_groups', 4)

        self.assertDictEquals(response, {
            'account': {
                'id': 2,
                'name': 'test account 2',
            },
            'campaign': {
                'id': 2,
                'name': 'test campaign 2',
                'landingMode': False,
            },
            'ad_group': {
                'id': 4,
                'name': 'test adgroup 4',
                'state': 2,
                'status': 2,
                'autopilot_state': 2,
                'active': 'stopped',
            }
        })

    def test_get_ad_group_no_access(self):
        # has other available
        response = self._get(1, 'ad_groups', 4)
        self.assertDictEqual(response, {
            'message': 'Ad Group does not exist',
            'error_code': 'MissingDataError'
        })

        # has nothing available
        response = self._get(4, 'ad_groups', 2)
        self.assertDictEqual(response, {
            'message': 'Ad Group does not exist',
            'error_code': 'MissingDataError'
        })


class NavigationTreeViewTest(TestCase):
    fixtures = ['test_navigation.yaml']

    def _get(self, user_id, filtered_sources=None):
        username = User.objects.get(pk=user_id).email
        self.client.login(username=username, password='secret')

        response = self.client.get(reverse('navigation_tree'),
                                   data={'filtered_sources': filtered_sources})

        response = json.loads(response.content)
        return response

    @patch('datetime.datetime', MockDatetime)
    def test_get(self):
        response = self._get(1)

        expected_response = [{
            "archived": False,
            "campaigns": [{
                "adGroups": [{
                    "archived": False,
                    "id": 1,
                    "name": "test adgroup 1",
                    "state": 1,
                    "status": 1,
                    "autopilot_state": 2,
                    "active": "active",
                }, {
                    "archived": False,
                    "id": 2,
                    "name": "test adgroup 2",
                    "state": 1,
                    "status": 2,  # past dates
                    "autopilot_state": 2,
                    "active": "inactive",
                }, {
                    "archived": False,
                    "id": 3,
                    "name": "test adgroup 3",
                    "state": 2,
                    "status": 2,
                    "autopilot_state": 2,
                    "active": "stopped",
                }],
                "archived": False,
                "id": 1,
                "name": "test campaign 1",
                "landingMode": False,
            }],
            "id": 1,
            "name": "test account 1",
        }]
        self.assertItemsEqual(response['data'], expected_response)

    @patch('datetime.datetime', MockDatetime)
    def test_get_filtered_sources(self):
        response = self._get(1, [2])

        expected_response = [{
            "archived": False,
            "campaigns": [{
                "adGroups": [{
                    "archived": False,
                    "id": 1,
                    "name": "test adgroup 1",
                    "state": 1,
                    "status": 2,  # source paused
                    "autopilot_state": 2,
                    "active": "inactive",
                }, {
                    "archived": False,
                    "id": 2,
                    "name": "test adgroup 2",
                    "state": 1,
                    "status": 2,
                    "autopilot_state": 2,
                    "active": "inactive",
                }, {
                    "archived": False,
                    "id": 3,
                    "name": "test adgroup 3",
                    "state": 2,
                    "status": 2,  # source paused
                    "autopilot_state": 2,
                    "active": "stopped",
                }],
                "landingMode": False,
                "archived": False,
                "id": 1,
                "name": "test campaign 1"
            }],
            "id": 1,
            "name": "test account 1",
        }]
        self.assertItemsEqual(response['data'], expected_response)

    @patch('datetime.datetime', MockDatetime)
    def test_get_archived_flag(self):

        # user has no right for archived flag
        response = self._get(2)

        expected_response = [{
            "campaigns": [{
                "adGroups": [
                    {
                        "id": 4,
                        "name": "test adgroup 4",
                        "state": 2,
                        "status": 2,
                        "autopilot_state": 2,
                        "active": "stopped",
                    }
                ],
                "id": 2,
                "name": "test campaign 2",
                "landingMode": False,
            }],
            "id": 2,
            "name": "test account 2",
        }]

        self.assertItemsEqual(response['data'], expected_response)

        # add user right for archived flag
        user = User.objects.get(pk=2)
        permission = Permission.objects.get(codename='view_archived_entities')
        user.user_permissions.add(permission)

        response = self._get(2)

        expected_response = [{
            "campaigns": [{
                "adGroups": [
                    {
                        "archived": True,
                        "id": 4,
                        "name": "test adgroup 4",
                        "state": 2,
                        "status": 2,
                        "autopilot_state": 2,
                        "active": "stopped",
                    }
                ],
                "id": 2,
                "name": "test campaign 2",
                "archived": False,
                "landingMode": False,
            }],
            "id": 2,
            "name": "test account 2",
            "archived": False,
        }]

        self.assertItemsEqual(response['data'], expected_response)

    def test_get_no_data(self):
        self.assertDictEqual(self._get(4), {"success": True})
