import datetime
import mock

from django.conf import settings
from django.test import TestCase
from django.http.request import HttpRequest

from actionlog import api_contentads
from actionlog import constants
from actionlog import models
from utils import test_helper, url_helper

import dash.models
import dash.constants
from zemauth.models import User


class ContentAdsApiTestCase(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        patcher_urlopen = mock.patch('utils.request_signer._secure_opener.open')
        self.addCleanup(patcher_urlopen.stop)

        mock_urlopen = patcher_urlopen.start()
        test_helper.prepare_mock_urlopen(mock_urlopen)

        self.credentials_encription_key = settings.CREDENTIALS_ENCRYPTION_KEY
        settings.CREDENTIALS_ENCRYPTION_KEY = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'

        self.maxDiff = None

    def tearDown(self):
        settings.CREDENTIALS_ENCRYPTION_KEY = self.credentials_encription_key

    @mock.patch('actionlog.models.datetime', test_helper.MockDateTime)
    def test_insert_content_ad(self):
        utcnow = datetime.datetime.utcnow()
        models.datetime.utcnow = classmethod(lambda cls: utcnow)

        content_ad_source = dash.models.ContentAdSource.objects.get(id=1)
        ad_group_source = dash.models.AdGroupSource.objects.get(
            ad_group=content_ad_source.content_ad.ad_group,
            source=content_ad_source.source
        )

        request = HttpRequest()
        request.user = User.objects.get(id=1)

        api_contentads.init_insert_content_ad_action(content_ad_source, request)

        action = models.ActionLog.objects.get(
            ad_group_source=ad_group_source,
        )

        self.assertEqual(action.action, constants.Action.INSERT_CONTENT_AD)
        self.assertEqual(action.action_type, constants.ActionType.AUTOMATIC)
        self.assertEqual(action.state, constants.ActionState.WAITING)

        expiration_dt = (utcnow + datetime.timedelta(minutes=models.ACTION_TIMEOUT_MINUTES)).\
            strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
        callback = url_helper.get_zwei_callback_url(action.id)

        ad_group_settings = dash.models.AdGroupSettings.objects.get(pk=1)
        payload = {
            'source': ad_group_source.source.source_type.type,
            'action': constants.Action.INSERT_CONTENT_AD,
            'expiration_dt': expiration_dt,
            'args': {
                'source_campaign_key': ad_group_source.source_campaign_key,
                'content_ad': {
                    'ad_group_id': content_ad_source.content_ad.ad_group_id,
                    'content_ad_id': content_ad_source.content_ad.id,
                    'source_content_ad_id': content_ad_source.source_content_ad_id,
                    'state': dash.constants.ContentAdSourceState.ACTIVE,
                    'title': content_ad_source.content_ad.title,
                    'url': content_ad_source.content_ad.url,
                    'submission_status': dash.constants.ContentAdSubmissionStatus.PENDING,
                    'image_id': content_ad_source.content_ad.image_id,
                    'image_width': content_ad_source.content_ad.image_width,
                    'image_height': content_ad_source.content_ad.image_height,
                    'image_hash': content_ad_source.content_ad.image_hash,
                    'display_url': content_ad_source.content_ad.display_url,
                    'brand_name': content_ad_source.content_ad.brand_name,
                    'description': content_ad_source.content_ad.description,
                    'call_to_action': content_ad_source.content_ad.call_to_action,
                    'tracking_slug': ad_group_source.source.tracking_slug,
                    'redirect_id': content_ad_source.content_ad.redirect_id,
                    'tracker_urls': content_ad_source.content_ad.tracker_urls
                },
            },
            'callback_url': callback
        }
        self.assertEqual(action.payload, payload)

        ad_group_source.source.source_type.available_actions.append(
            dash.constants.SourceAction.UPDATE_TRACKING_CODES_ON_CONTENT_ADS
        )
        ad_group_source.source.source_type.save()

        ad_group_source.can_manage_content_ads = True
        ad_group_source.save(request)

        new_ad_group_settings = ad_group_settings.copy_settings()
        new_ad_group_settings.tracking_code = 'a=b'
        new_ad_group_settings.save(request)

        api_contentads.init_insert_content_ad_action(content_ad_source, request)

        action = models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
        ).latest('created_dt')

        self.assertEqual(action.action, constants.Action.INSERT_CONTENT_AD)
        self.assertEqual(action.action_type, constants.ActionType.AUTOMATIC)
        self.assertEqual(action.state, constants.ActionState.WAITING)

        expiration_dt = (utcnow + datetime.timedelta(minutes=models.ACTION_TIMEOUT_MINUTES)).\
            strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
        callback = url_helper.get_zwei_callback_url(action.id)

        payload = {
            'source': ad_group_source.source.source_type.type,
            'action': constants.Action.INSERT_CONTENT_AD,
            'expiration_dt': expiration_dt,
            'args': {
                'source_campaign_key': ad_group_source.source_campaign_key,
                'content_ad': {
                    'ad_group_id': content_ad_source.content_ad.ad_group_id,
                    'content_ad_id': content_ad_source.content_ad.id,
                    'source_content_ad_id': content_ad_source.source_content_ad_id,
                    'state': dash.constants.ContentAdSourceState.ACTIVE,
                    'title': content_ad_source.content_ad.title,
                    'url': content_ad_source.content_ad.url_with_tracking_codes(
                        url_helper.combine_tracking_codes(
                            new_ad_group_settings.get_tracking_codes(),
                            ad_group_source.get_tracking_ids(),
                        )
                    ),
                    'submission_status': dash.constants.ContentAdSubmissionStatus.PENDING,
                    'image_id': content_ad_source.content_ad.image_id,
                    'image_width': content_ad_source.content_ad.image_width,
                    'image_height': content_ad_source.content_ad.image_height,
                    'image_hash': content_ad_source.content_ad.image_hash,
                    'display_url': content_ad_source.content_ad.display_url,
                    'brand_name': content_ad_source.content_ad.brand_name,
                    'description': content_ad_source.content_ad.description,
                    'call_to_action': content_ad_source.content_ad.call_to_action,
                    'tracking_slug': ad_group_source.source.tracking_slug,
                    'redirect_id': content_ad_source.content_ad.redirect_id,
                    'tracker_urls': content_ad_source.content_ad.tracker_urls
                },
            },
            'callback_url': callback
        }
        self.assertEqual(action.payload, payload)

    @mock.patch('actionlog.models.datetime', test_helper.MockDateTime)
    def test_insert_content_ad_batch(self):
        utcnow = datetime.datetime.utcnow()
        models.datetime.utcnow = classmethod(lambda cls: utcnow)

        content_ad_source = dash.models.ContentAdSource.objects.get(pk=1)

        ad_group_source = dash.models.AdGroupSource.objects.get(
            ad_group=content_ad_source.content_ad.ad_group,
            source=content_ad_source.source
        )

        batch = dash.models.UploadBatch.objects.get(pk=1)

        request = HttpRequest()
        request.user = User.objects.create(email='user@example.com')

        action = api_contentads.init_insert_content_ad_batch(
            batch, content_ad_source.source, request, send=False)

        expiration_dt = (utcnow + datetime.timedelta(minutes=models.ACTION_TIMEOUT_MINUTES))
        callback = url_helper.get_zwei_callback_url(action.id)

        self.assertEqual(action.payload, {
            'source': ad_group_source.source.source_type.type,
            'action': constants.Action.INSERT_CONTENT_AD_BATCH,
            'expiration_dt': expiration_dt,
            'args': {
                'source_campaign_key': ad_group_source.source_campaign_key,
                'content_ads': [{
                    'ad_group_id': content_ad_source.content_ad.ad_group_id,
                    'content_ad_id': content_ad_source.content_ad.id,
                    'source_content_ad_id': content_ad_source.source_content_ad_id,
                    'state': dash.constants.ContentAdSourceState.ACTIVE,
                    'title': content_ad_source.content_ad.title,
                    'url': content_ad_source.content_ad.url,
                    'submission_status': dash.constants.ContentAdSubmissionStatus.PENDING,
                    'image_id': content_ad_source.content_ad.image_id,
                    'image_width': content_ad_source.content_ad.image_width,
                    'image_height': content_ad_source.content_ad.image_height,
                    'image_hash': content_ad_source.content_ad.image_hash,
                    'display_url': content_ad_source.content_ad.display_url,
                    'brand_name': content_ad_source.content_ad.brand_name,
                    'description': content_ad_source.content_ad.description,
                    'call_to_action': content_ad_source.content_ad.call_to_action,
                    'tracking_slug': ad_group_source.source.tracking_slug,
                    'redirect_id': content_ad_source.content_ad.redirect_id,
                    'tracker_urls': content_ad_source.content_ad.tracker_urls
                }],
                'extra': {}
            },
            'callback_url': callback
        })

    def test_insert_content_ad_batch_gravity(self):
        content_ad_source = dash.models.ContentAdSource.objects.get(pk=2)

        ad_group_source = dash.models.AdGroupSource.objects.get(
            ad_group=content_ad_source.content_ad.ad_group,
            source=content_ad_source.source
        )

        ad_group_settings = ad_group_source.ad_group.get_current_settings()

        batch = dash.models.UploadBatch.objects.get(pk=1)

        request = HttpRequest()
        request.user = User.objects.create(email='user@example.com')

        action = api_contentads.init_insert_content_ad_batch(
            batch, content_ad_source.source, request, send=False)

        self.assertEqual(action.payload['args']['extra'], {
            'batch_name': batch.name,
            'campaign_name': ad_group_source.get_external_name(),
            'ad_group_id': ad_group_source.ad_group.id,
            'user_email': request.user.email,
            'brand_name': ad_group_settings.brand_name
        })

    @mock.patch('actionlog.models.datetime', test_helper.MockDateTime)
    def test_update_content_ad(self):
        utcnow = datetime.datetime.utcnow()
        models.datetime.utcnow = classmethod(lambda cls: utcnow)

        content_ad_source = dash.models.ContentAdSource.objects.get(id=2)
        ad_group_source = dash.models.AdGroupSource.objects.get(
            ad_group=content_ad_source.content_ad.ad_group,
            source=content_ad_source.source
        )

        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

        changes = {
            'state': dash.constants.ContentAdSourceState.INACTIVE,
        }

        api_contentads.init_update_content_ad_action(content_ad_source, changes, request)

        action = models.ActionLog.objects.get(
            ad_group_source=ad_group_source,
        )

        self.assertEqual(action.action, constants.Action.UPDATE_CONTENT_AD)
        self.assertEqual(action.action_type, constants.ActionType.AUTOMATIC)
        self.assertEqual(action.state, constants.ActionState.WAITING)

        expiration_dt = (utcnow + datetime.timedelta(minutes=models.ACTION_TIMEOUT_MINUTES)).\
            strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
        callback = url_helper.get_zwei_callback_url(action.id)
        payload = {
            'source': ad_group_source.source.source_type.type,
            'action': constants.Action.UPDATE_CONTENT_AD,
            'expiration_dt': expiration_dt,
            'args': {
                'source_campaign_key': ad_group_source.source_campaign_key,
                'changes': {
                    'state': dash.constants.ContentAdSourceState.INACTIVE,
                },
                'content_ad': {
                    'ad_group_id': content_ad_source.content_ad.ad_group_id,
                    'content_ad_id': content_ad_source.content_ad.id,
                    'source_content_ad_id': content_ad_source.source_content_ad_id,
                    'state': dash.constants.ContentAdSourceState.INACTIVE,
                    'title': content_ad_source.content_ad.title,
                    'url': content_ad_source.content_ad.url,
                    'submission_status': content_ad_source.submission_status,
                    'image_id': content_ad_source.content_ad.image_id,
                    'image_width': content_ad_source.content_ad.image_width,
                    'image_height': content_ad_source.content_ad.image_height,
                    'image_hash': content_ad_source.content_ad.image_hash,
                    'display_url': content_ad_source.content_ad.display_url,
                    'brand_name': content_ad_source.content_ad.brand_name,
                    'description': content_ad_source.content_ad.description,
                    'call_to_action': content_ad_source.content_ad.call_to_action,
                    'tracking_slug': ad_group_source.source.tracking_slug,
                    'redirect_id': content_ad_source.content_ad.redirect_id,
                    'tracker_urls': content_ad_source.content_ad.tracker_urls
                },
            },
            'callback_url': callback
        }
        self.assertEqual(action.payload, payload)

    @mock.patch('actionlog.models.datetime', test_helper.MockDateTime)
    def test_get_content_ad_status(self):
        utcnow = datetime.datetime.utcnow()
        models.datetime.utcnow = classmethod(lambda cls: utcnow)

        ad_group_source = dash.models.AdGroupSource.objects.get(id=1)

        order = models.ActionLogOrder.objects.create(
            order_type=constants.ActionLogOrderType.GET_CONTENT_AD_STATUS)
        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

        api_contentads.init_get_content_ad_status_action(ad_group_source, order, request)

        action = models.ActionLog.objects.get(
            ad_group_source=ad_group_source,
        )

        self.assertEqual(action.action, constants.Action.GET_CONTENT_AD_STATUS)
        self.assertEqual(action.action_type, constants.ActionType.AUTOMATIC)
        self.assertEqual(action.state, constants.ActionState.WAITING)
        self.assertEqual(action.order, order)

        expiration_dt = (utcnow + datetime.timedelta(minutes=models.ACTION_TIMEOUT_MINUTES)).\
            strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
        callback = url_helper.get_zwei_callback_url(action.id)
        payload = {
            'source': ad_group_source.source.source_type.type,
            'action': constants.Action.GET_CONTENT_AD_STATUS,
            'expiration_dt': expiration_dt,
            'args': {
                'source_campaign_key': ad_group_source.source_campaign_key,
            },
            'callback_url': callback
        }
        self.assertEqual(action.payload, payload)

    @mock.patch('actionlog.models.datetime', test_helper.MockDateTime)
    def test_submit_ad_group(self):
        utcnow = datetime.datetime.utcnow()
        models.datetime.utcnow = classmethod(lambda cls: utcnow)

        content_ad_source = dash.models.ContentAdSource.objects.get(id=1)
        ad_group_source = dash.models.AdGroupSource.objects.get(id=1)

        api_contentads.init_submit_ad_group_action(ad_group_source, content_ad_source, None)

        action = models.ActionLog.objects.get(
            ad_group_source=ad_group_source,
        )

        self.assertEqual(action.action, constants.Action.SUBMIT_AD_GROUP)
        self.assertEqual(action.action_type, constants.ActionType.AUTOMATIC)
        self.assertEqual(action.state, constants.ActionState.WAITING)

        expiration_dt = (utcnow + datetime.timedelta(minutes=models.ACTION_TIMEOUT_MINUTES)).\
            strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
        callback = url_helper.get_zwei_callback_url(action.id)

        ad_group_settings = dash.models.AdGroupSettings.objects.get(pk=1)
        payload = {
            'source': ad_group_source.source.source_type.type,
            'action': constants.Action.SUBMIT_AD_GROUP,
            'expiration_dt': expiration_dt,
            'args': {
                'source_campaign_key': ad_group_source.source_campaign_key,
                'content_ad': {
                    'ad_group_id': content_ad_source.content_ad.ad_group_id,
                    'content_ad_id': content_ad_source.content_ad.id,
                    'source_content_ad_id': content_ad_source.source_content_ad_id,
                    'state': dash.constants.ContentAdSourceState.ACTIVE,
                    'title': content_ad_source.content_ad.title,
                    'url': content_ad_source.content_ad.url,
                    'submission_status': content_ad_source.submission_status,
                    'image_id': content_ad_source.content_ad.image_id,
                    'image_hash': content_ad_source.content_ad.image_hash,
                    'image_width': content_ad_source.content_ad.image_width,
                    'image_height': content_ad_source.content_ad.image_height,
                    'display_url': ad_group_settings.display_url,
                    'brand_name': ad_group_settings.brand_name,
                    'description': ad_group_settings.description,
                    'call_to_action': ad_group_settings.call_to_action,
                    'tracking_slug': ad_group_source.source.tracking_slug,
                    'redirect_id': content_ad_source.content_ad.redirect_id,
                    'tracker_urls': content_ad_source.content_ad.tracker_urls
                },
            },
            'callback_url': callback
        }
        self.assertEqual(action.payload, payload)
