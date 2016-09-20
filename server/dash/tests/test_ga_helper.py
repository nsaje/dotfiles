from django.test import TestCase, override_settings
from mock import patch

from googleapiclient.errors import HttpError

from dash import ga_helper


@override_settings(R1_DEMO_MODE=False)
class GAHelperTest(TestCase):

    @staticmethod
    def _mock_response(permissions):
        return {
            u'profileCount': 1,
            u'kind': u'analytics#webproperty',
            u'name': u'Ideas & Advice',
            u'level': u'STANDARD',
            u'created': u'2014-01-17T18:21:05.520Z',
            u'updated': u'2014-01-17T18:21:06.765Z',
            u'websiteUrl': u'http://example.com/',
            u'internalWebPropertyId': u'123',
            u'childLink': {u'href': u'https://www.example.com/profiles', u'type': u'analytics#profiles'},
            u'industryVertical': u'SHOPPING',
            u'parentLink': {u'href': u'https://www.example.com/accounts/', u'type': u'analytics#account'},
            u'permissions': {u'effective': permissions},
            u'id': u'UA-123456789-1',
            u'selfLink': u'https://www.example.com/',
            u'accountId': u'123456789',
        }

    def setUp(self):
        self.patcher = patch.object(ga_helper, '_management_service')
        self.mock_service = self.patcher.start()
        self.mock_get = self.mock_service.management().webproperties().get

    def tearDown(self):
        self.patcher.stop()

    def test_is_readable(self):
        self.mock_get().execute.return_value = self._mock_response(['READ_AND_ANALYZE'])
        valid = ga_helper.is_readable('UA-123456789-1')
        self.mock_get.assert_called_with(accountId='123456789', webPropertyId='UA-123456789-1')
        self.assertEqual(True, valid)

    def test_incorrect_permissions(self):
        self.mock_get().execute.return_value = self._mock_response(['MANAGE_USERS'])
        valid = ga_helper.is_readable('UA-123456789-1')
        self.mock_get.assert_called_with(accountId='123456789', webPropertyId='UA-123456789-1')
        self.assertEqual(False, valid)

    def test_insufficient_permissions(self):
        content = '{"error":{"errors":[{"domain":"global","reason":"insufficientPermissions","message":"User does not have sufficient permissions for this account."}],"code":403,"message":"User does not have sufficient permissions for this account."}}'
        httperror = HttpError(None, content)
        self.mock_get().execute.side_effect = httperror
        valid = ga_helper.is_readable('UA-123456789-1')
        self.assertEqual(False, valid)

    def test_ga_error(self):
        content = '{"error":{"errors":[{"domain":"global","reason":"rateLimitExceeded","message":"Rate limit exceeded"}],"code":403,"message":"Rate limit exceeded"}}'
        httperror = HttpError(None, content)
        self.mock_get().execute.side_effect = httperror
        with self.assertRaises(HttpError):
            ga_helper.is_readable('UA-123456789-1')
