import json

from mock import patch, Mock

from django.test import TestCase, override_settings
from django.conf import settings

import dash.models
from utils import redirector_helper
from utils.test_helper import ListMatcher


@override_settings(
    R1_API_SIGN_KEY='AAAAAAAAAAAAAAAAAAAAAAAA',
    R1_VALIDATE_API_URL='https://r1.zemanta.com/api/validate/',
    R1_DEMO_MODE=False
)
@patch('utils.request_signer._secure_opener.open')
class ValidateURLTest(TestCase):
    def test_validate_url(self, mock_urlopen):
        url = "https://example.com"

        response = Mock()
        response.read.return_value = json.dumps({"data": True, "status": "ok"})
        response.getcode = lambda: 200
        mock_urlopen.return_value = response

        self.assertEqual(redirector_helper.validate_url(url, 1), True)

        call = mock_urlopen.call_args[0][0]

        self.assertEqual(call.get_full_url(), settings.R1_VALIDATE_API_URL)
        self.assertEqual(call.data, json.dumps({"url": url, "adgroupid": 1}))

    def test_code_error(self, mock_urlopen):
        url = 'https://example.com/image'

        response = Mock()
        response.getcode = lambda: 500
        mock_urlopen.return_value = response

        with self.assertRaises(Exception):
            redirector_helper.validate_url(url, 1)
        self.assertEqual(len(mock_urlopen.call_args_list), 3)

    def test_status_not_success(self, mock_urlopen):
        url = 'https://example.com/image'

        response = Mock()
        response.read.return_value = '{"status": "error"}'
        response.getcode = lambda: 200
        mock_urlopen.return_value = response

        with self.assertRaises(Exception):
            redirector_helper.validate_url(url, 1)
        self.assertEqual(len(mock_urlopen.call_args_list), 3)


@override_settings(
    R1_REDIRECTS_API_URL='https://r1.example.com/api/redirects/',
    R1_REDIRECTS_ADGROUP_API_URL='https://r1.example.com/api/redirects/',
    R1_API_SIGN_KEY='AAAAAAAAAAAAAAAAAAAAAAAA',
    R1_DEMO_MODE=False
)
@patch('utils.request_signer._secure_opener.open')
class UpdateRedirectTest(TestCase):
    def test_update_redirect(self, mock_urlopen):
        url = "https://example.com"

        redirect_id = "u123456"

        response = Mock()
        response.read.return_value = json.dumps({
            "status": "ok",
            "data": {
                "redirectid": redirect_id,
                "redirect": {
                    "url": url
                }
            }
        })
        response.getcode = lambda: 200
        mock_urlopen.return_value = response

        response_dict = redirector_helper.update_redirect(url, redirect_id)
        self.assertEqual(response_dict["redirectid"], redirect_id)

        call = mock_urlopen.call_args[0][0]

        self.assertEqual(call.get_full_url(), settings.R1_REDIRECTS_API_URL + redirect_id + '/')
        self.assertEqual(call.data, json.dumps({"url": "https://example.com"}))


@override_settings(
    R1_REDIRECTS_BATCH_API_URL='https://r1.example.com/api/redirects/redirectsbatch/',
    R1_API_SIGN_KEY='AAAAAAAAAAAAAAAAAAAAAAAA',
    R1_DEMO_MODE=False
)
@patch('utils.request_signer._secure_opener.open')
class InsertRedirectsBatchTest(TestCase):

    fixtures = ['test_api.yaml']

    def test_insert_redirects(self, mock_urlopen):
        content_ads = [
            dash.models.ContentAd.objects.get(id=1),
            dash.models.ContentAd.objects.get(id=2),
        ]

        redirect_id = "u123456"
        response = Mock()
        response.read.return_value = json.dumps({
            "status": "ok",
            "data": {
                1: {
                    "redirectid": redirect_id,
                    "redirect": {
                        "url": content_ads[0].url
                    },
                },
                2: {
                    "redirectid": redirect_id,
                    "redirect": {
                        "url": content_ads[1].url
                    },
                },
            },
        })
        response.getcode = lambda: 200
        mock_urlopen.return_value = response

        response_dict = redirector_helper.insert_redirects(content_ads)
        for content_ad in content_ads:
            self.assertEqual(response_dict[str(content_ad.id)]["redirectid"], redirect_id)

        call = mock_urlopen.call_args[0][0]

        self.assertEqual(call.get_full_url(), settings.R1_REDIRECTS_BATCH_API_URL)
        self.assertEqual(call.data, json.dumps([
            {"url": content_ads[0].url, "creativeid": 1, "adgroupid": content_ads[0].ad_group_id, 'noclickthroughresolve': False},
            {"url": content_ads[1].url, "creativeid": 2, "adgroupid": content_ads[1].ad_group_id, 'noclickthroughresolve': False},
        ]))

    @override_settings(
        R1_DEMO_MODE=True,
    )
    def test_demo_mode(self, mock_urlopen):
        content_ads = [
            dash.models.ContentAd.objects.get(id=1),
            dash.models.ContentAd.objects.get(id=2),
        ]
        response_dict = redirector_helper.insert_redirects(content_ads)
        for content_ad in content_ads:
            self.assertEqual(response_dict[str(content_ad.id)], {
                'redirect': {'url': 'http://example.com/FAKE'},
                'redirectid': 'XXXXXXXXXXXXX'
            })
        self.assertFalse(mock_urlopen.called)


@override_settings(
    R1_REDIRECTS_API_URL='https://r1.example.com/api/redirects/',
    R1_REDIRECTS_ADGROUP_API_URL='https://r1.example.com/api/redirects/',
    R1_API_SIGN_KEY='AAAAAAAAAAAAAAAAAAAAAAAA',
    R1_DEMO_MODE=False
)
@patch('utils.request_signer._secure_opener.open')
class InsertAdGroupTest(TestCase):

    fixtures = ['test_api.yaml']

    def test_insert_adgroup(self, mock_urlopen):
        ad_group = dash.models.AdGroup.objects.get(id=1)

        new_ad_group_settings = ad_group.get_current_settings().copy_settings()
        new_ad_group_settings.tracking_code = 'lala=1'
        new_ad_group_settings.redirect_pixel_urls = []
        new_ad_group_settings.redirect_javascript = ''
        new_ad_group_settings.save(None)

        new_campaign_settings = ad_group.campaign.get_current_settings().copy_settings()
        new_campaign_settings.enable_ga_tracking = True
        new_campaign_settings.enable_adobe_tracking = False
        new_campaign_settings.adobe_tracking_param = 'cid'
        new_campaign_settings.save(None)

        response = Mock()
        response.read.return_value = '{"status": "ok"}'
        response.getcode = lambda: 200
        mock_urlopen.return_value = response

        redirector_helper.insert_adgroup(
            ad_group,
            ad_group.get_current_settings(),
            ad_group.campaign.get_current_settings(),
        )

        call = mock_urlopen.call_args[0][0]

        self.assertEqual(call.get_full_url(), settings.R1_REDIRECTS_ADGROUP_API_URL.format(adgroup=ad_group.id))
        self.assertEqual(call.get_method(), 'PUT')

        self.assertEqual(json.loads(call.data), {
            "campaignid": ad_group.campaign_id,
            "accountid": ad_group.campaign.account_id,
            "trackingcode": ad_group.get_current_settings().get_tracking_codes(),
            "enablegatracking": True,
            "enableadobetracking": False,
            "adobetrackingparam": 'cid',
            "clickcappingdailyadgroupmaxclicks": 10,
        })

        new_ad_group_settings = ad_group.get_current_settings().copy_settings()
        new_ad_group_settings.redirect_pixel_urls = ['http://a.com', 'http://b.com']
        new_ad_group_settings.redirect_javascript = 'alert("a");'
        new_ad_group_settings.click_capping_daily_ad_group_max_clicks = 10
        new_ad_group_settings.save(None)

        redirector_helper.insert_adgroup(
            ad_group,
            ad_group.get_current_settings(),
            ad_group.campaign.get_current_settings(),
        )

        call = mock_urlopen.call_args[0][0]

        self.assertEqual(call.get_full_url(), settings.R1_REDIRECTS_ADGROUP_API_URL.format(adgroup=ad_group.id))
        self.assertEqual(call.get_method(), 'PUT')
        self.assertEqual(json.loads(call.data), {
            "campaignid": ad_group.campaign_id,
            "accountid": ad_group.campaign.account_id,
            "trackingcode": ad_group.get_current_settings().get_tracking_codes(),
            "enablegatracking": True,
            "enableadobetracking": False,
            "adobetrackingparam": 'cid',
            "specialredirecttrackers": ['http://a.com', 'http://b.com'],
            "specialredirectjavascript": 'alert("a");',
            "clickcappingdailyadgroupmaxclicks": 10,
        })

    def test_code_error(self, mock_urlopen):
        response = Mock()
        response.getcode = lambda: 500
        mock_urlopen.return_value = response

        ad_group = dash.models.AdGroup.objects.get(id=1)
        with self.assertRaises(Exception):
            redirector_helper.insert_adgroup(
                ad_group,
                ad_group.get_current_settings(),
                ad_group.campaign.get_current_settings()
            )
        self.assertEqual(len(mock_urlopen.call_args_list), 3)

    def test_status_not_success(self, mock_urlopen):
        response = Mock()
        response.read.return_value = '{"status": "error"}'
        response.getcode = lambda: 200
        mock_urlopen.return_value = response

        ad_group = dash.models.AdGroup.objects.get(id=1)
        with self.assertRaises(Exception):
            redirector_helper.insert_adgroup(
                ad_group,
                ad_group.get_current_settings(),
                ad_group.campaign.get_current_settings()
            )
        self.assertEqual(len(mock_urlopen.call_args_list), 3)


@override_settings(
    R1_REDIRECTS_API_URL='https://r1.example.com/api/redirects/',
    R1_REDIRECTS_ADGROUP_API_URL='https://r1.example.com/api/redirects/',
    R1_API_SIGN_KEY='AAAAAAAAAAAAAAAAAAAAAAAA',
    R1_DEMO_MODE=False
)
@patch('utils.request_signer._secure_opener.open')
class GetAdgroupTest(TestCase):

    def test_get_adgroup(self, mock_urlopen):
        response = Mock()
        response.read.return_value = ('{"status":"ok","data":{"trackingcode":"xyz","enablegatracking":true,'
                                      '"enableadobetracking":false,"adobetrackingparam":"",'
                                      '"createddt":"2015-02-01T22:00:00Z","modifieddt":"2015-11-09T15:30:24.463752Z",'
                                      '"clickcappingdailyadgroupmaxclicks":10}}')
        response.getcode = lambda: 200
        mock_urlopen.return_value = response

        ad_group_id = 123

        ad_group_dict = redirector_helper.get_adgroup(ad_group_id)

        self.assertDictEqual(ad_group_dict, {
            'tracking_code': 'xyz',
            'enable_ga_tracking': True,
            'enable_adobe_tracking': False,
            'adobe_tracking_param': '',
            'click_capping_daily_ad_group_max_clicks': 10,
        })

        call = mock_urlopen.call_args[0][0]

        self.assertEqual(call.get_full_url(), settings.R1_REDIRECTS_ADGROUP_API_URL.format(adgroup=123))
        self.assertEqual(call.get_method(), 'GET')
        self.assertEqual(call.data, None)

    def test_get_adgroup_non_existent(self, mock_urlopen):
        response = Mock()
        response.getcode = lambda: 404
        mock_urlopen.return_value = response

        with self.assertRaises(Exception):
            redirector_helper.get_adgroup(100)

        self.assertEqual(len(mock_urlopen.call_args_list), 3, "Should retry the call 3-times")


@override_settings(
    R1_CUSTOM_AUDIENCE_API_URL='https://r1.example.com/api/audience/{audience_id}',
    R1_API_SIGN_KEY='AAAAAAAAAAAAAAAAAAAAAAAA',
    R1_DEMO_MODE=False
)
@patch('utils.request_signer._secure_opener.open')
class UpsertAudienceTest(TestCase):

    fixtures = ['test_k1_api.yaml']

    def test_upsert_audience(self, mock_urlopen):
        response = Mock()
        response.read.return_value = '{"status": "ok", "data":{"audienceid":"1"}}'
        response.getcode = lambda: 200
        mock_urlopen.return_value = response

        audience = dash.models.Audience.objects.get(pk=1)
        resp = redirector_helper.upsert_audience(audience)

        self.assertDictEqual(resp, {u'audienceid': u'1'})

        call = mock_urlopen.call_args[0][0]

        self.assertEqual(call.get_full_url(), settings.R1_CUSTOM_AUDIENCE_API_URL.format(audience_id=1))
        self.assertEqual(call.get_method(), 'PUT')
        expected = {
            u'id': u'1',
            u'accountid': 1,
            u'pixieslug': u'testslug1',
            u'archived': False,
            u'rules': ListMatcher(
                [{u'id': u'1', u'type': 1, u'value': u'dummy'}, {u'id': u'2', u'type': 2, u'value': u'dummy2'}]),
            u'pixels': ListMatcher(
                [{u'url': u'http://www.fb.com/pixelendpoint', u'type': u'facebook'},
                 {u'url': u'http://www.y.com/pixelendpoint', u'type': u'yahoo'},
                 {u'url': u'http://www.ob.com/pixelendpoint', u'type': u'outbrain'}]
            ),
            u'ttl': 90,
            u'modifieddt': u'2015-02-23T00:00:00Z'
        }
        self.assertJSONEqual(call.data, expected)

    def test_upsert_audience_error(self, mock_urlopen):
        response = Mock()
        response.getcode = lambda: 400
        mock_urlopen.return_value = response

        audience = dash.models.Audience.objects.get(pk=1)
        with self.assertRaises(Exception):
            redirector_helper.upsert_audience(audience)

        self.assertEqual(len(mock_urlopen.call_args_list), 3, "Should retry the call 3-times")


@override_settings(
    R1_CUSTOM_AUDIENCE_API_URL='https://r1.example.com/api/audience/{audience_id}',
    R1_API_SIGN_KEY='AAAAAAAAAAAAAAAAAAAAAAAA',
    R1_DEMO_MODE=False
)
@patch('utils.request_signer._secure_opener.open')
class DeleteAudienceTest(TestCase):

    fixtures = ['test_k1_api.yaml']

    def test_delete_audience(self, mock_urlopen):
        response = Mock()
        response.read.return_value = '{"status": "ok", "data":{"audienceid":"1"}}'
        response.getcode = lambda: 200
        mock_urlopen.return_value = response

        resp = redirector_helper.delete_audience(1)
        self.assertDictEqual(resp, {u'audienceid': u'1'})

        call = mock_urlopen.call_args[0][0]

        self.assertEqual(call.get_full_url(), settings.R1_CUSTOM_AUDIENCE_API_URL.format(audience_id=1))
        self.assertEqual(call.get_method(), 'DELETE')
        self.assertEqual(call.data, None)

    def test_delete_audience_error(self, mock_urlopen):
        response = Mock()
        response.getcode = lambda: 400
        mock_urlopen.return_value = response

        with self.assertRaises(Exception):
            redirector_helper.delete_audience(1)

        self.assertEqual(len(mock_urlopen.call_args_list), 3, "Should retry the call 3-times")


@override_settings(
    R1_PIXEL_URL='https://r1.example.com/api/pixel/{account_id}/{slug}/',
    R1_API_SIGN_KEY='AAAAAAAAAAAAAAAAAAAAAAAA',
    R1_DEMO_MODE=False
)
@patch('utils.request_signer._secure_opener.open')
class UpdatePixelTestCase(TestCase):

    fixtures = ['test_k1_api.yaml']

    def test_update_pixel(self, mock_urlopen):
        response = Mock()
        response.read.return_value = '{"status": "ok"}'
        response.getcode = lambda: 200
        mock_urlopen.return_value = response

        conversion_pixel = dash.models.ConversionPixel.objects.get(pk=1)
        conversion_pixel.redirect_url = 'http://test.com'
        redirector_helper.update_pixel(conversion_pixel)

        call = mock_urlopen.call_args[0][0]

        self.assertEqual(call.get_full_url(), 'https://r1.example.com/api/pixel/1/testslug1/')
        self.assertEqual(call.get_method(), 'PUT')
        expected = {
            'redirecturl': 'http://test.com',
        }
        self.assertJSONEqual(call.data, expected)

    def test_update_pixel_error(self, mock_urlopen):
        response = Mock()
        response.getcode = lambda: 400
        mock_urlopen.return_value = response

        conversion_pixel = dash.models.ConversionPixel.objects.get(pk=1)
        with self.assertRaises(Exception):
            redirector_helper.update_pixel(conversion_pixel)

        self.assertEqual(len(mock_urlopen.call_args_list), 3, "Should retry the call 3-times")
