import decimal
import datetime
import mock

from django.conf import settings
from django.test import TestCase
from django.http.request import HttpRequest

import actionlog.constants
import actionlog.models

from dash import models
from dash import api
from dash import constants

from zemauth.models import User

from utils import test_helper


class UpdateContentAdSourceState(TestCase):
    fixtures = ['test_api.yaml']

    def test_update_multiple_content_ad_source_states(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        content_ad_data = [{
            'id': 1,
            'state': 2,
            'submission_status': 2
        }]

        api.update_multiple_content_ad_source_states(ad_group_source, content_ad_data)

        content_ad_source = models.ContentAdSource.objects.get(pk=1)

        self.assertEqual(content_ad_source.source_state, content_ad_data[0]['state'])
        self.assertEqual(content_ad_source.submission_status, content_ad_data[0]['submission_status'])

    def test_update_content_ad_source_state(self):
        content_ad_source = models.ContentAdSource.objects.get(pk=1)
        data = {'source_state': 2, 'submission_status': 2}

        api.update_content_ad_source_state(content_ad_source, data)

        content_ad_source = models.ContentAdSource.objects.get(pk=1)
        self.assertEqual(content_ad_source.source_state, data['source_state'])
        self.assertEqual(content_ad_source.submission_status, data['submission_status'])


class UpdateAdGroupSourceState(TestCase):
    fixtures = ['test_api.yaml']

    def setUp(self):
        self.ad_group_source = models.AdGroupSource.objects.get(id=1)

    def test_should_update_if_changed(self):
        latest_state = models.AdGroupSourceState.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        conf = {
            'state': 2,
            'cpc_cc': 500,
            'daily_budget_cc': 10000
        }

        api.update_ad_group_source_state(self.ad_group_source, conf)

        new_latest_state = models.AdGroupSourceState.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertNotEqual(new_latest_state.id, latest_state.id)
        self.assertEqual(new_latest_state.state, conf['state'])
        self.assertEqual(float(new_latest_state.cpc_cc), 0.05)
        self.assertEqual(float(new_latest_state.daily_budget_cc), 1.0)

    def test_should_not_update_if_unchanged(self):
        latest_state = models.AdGroupSourceState.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        conf = {
            'state': latest_state.state,
            'cpc_cc': int(latest_state.cpc_cc * 10000),
            'daily_budget_cc': int(latest_state.daily_budget_cc * 10000)
        }

        api.update_ad_group_source_state(self.ad_group_source, conf)

        new_latest_state = models.AdGroupSourceState.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertEqual(new_latest_state.id, latest_state.id)

    def test_should_update_if_no_state_yet(self):
        self.assertTrue(
            models.AdGroupSourceState.objects.filter(ad_group_source=self.ad_group_source).count() > 0
        )
        models.AdGroupSourceState.objects.filter(ad_group_source=self.ad_group_source).delete()

        conf = {
            'state': 2,
            'cpc_cc': 500,
            'daily_budget_cc': 10000
        }

        api.update_ad_group_source_state(self.ad_group_source, conf)

        new_latest_state = models.AdGroupSourceState.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertEqual(new_latest_state.state, conf['state'])
        self.assertEqual(float(new_latest_state.cpc_cc), 0.05)
        self.assertEqual(float(new_latest_state.daily_budget_cc), 1.0)

        self.assertEqual(
            models.AdGroupSourceState.objects.filter(ad_group_source=self.ad_group_source).count(),
            1
        )

    def test_should_update_if_latest_settings(self):
        latest_state = models.AdGroupSourceState.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        conf = {
            'state': 2,
            'cpc_cc': 500,
            'daily_budget_cc': 10000
        }

        api.update_ad_group_source_state(self.ad_group_source, conf)

        new_latest_state = models.AdGroupSourceState.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertNotEqual(new_latest_state.id, latest_state.id)
        self.assertEqual(new_latest_state.state, conf['state'])
        self.assertEqual(float(new_latest_state.cpc_cc), 0.05)
        self.assertEqual(float(new_latest_state.daily_budget_cc), 1.0)

    def test_should_disregard_null_and_unspecified_fields(self):
        latest_state = models.AdGroupSourceState.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        conf = {
            'state': 2,
            'cpc_cc': None,
        }

        api.update_ad_group_source_state(self.ad_group_source, conf)

        new_latest_state = models.AdGroupSourceState.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertNotEqual(new_latest_state.id, latest_state.id)
        self.assertEqual(new_latest_state.state, conf['state'])
        self.assertEqual(new_latest_state.cpc_cc, latest_state.cpc_cc)
        self.assertEqual(new_latest_state.daily_budget_cc, latest_state.daily_budget_cc)


class AdGroupSourceSettingsWriterTest(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        self.ad_group_source = models.AdGroupSource.objects.get(id=1)
        self.writer = api.AdGroupSourceSettingsWriter(self.ad_group_source)
        self.ad_group_settings = \
            models.AdGroupSettings.objects \
                .filter(ad_group=self.ad_group_source.ad_group) \
                .latest('created_dt')
        assert self.ad_group_settings.state == 2

    def test_can_not_trigger_action_if_ad_group_disabled(self):
        self.assertFalse(self.writer.can_trigger_action())

    def test_can_trigger_action_if_ad_group_enabled(self):
        request = HttpRequest()
        request.user = User(id=1)

        self.ad_group_settings.state = 1
        self.ad_group_settings.save(request)
        self.assertTrue(self.writer.can_trigger_action())

    def test_should_write_if_no_settings_yet(self):
        self.assertTrue(
            models.AdGroupSourceSettings.objects.filter(ad_group_source=self.ad_group_source).count() > 0
        )
        # delete all ad_group_source_settings
        models.AdGroupSourceSettings.objects.filter(ad_group_source=self.ad_group_source).delete()

        request = HttpRequest()
        request.user = User(id=1)

        self.writer.set({'state': 1}, request)

        self.assertTrue(
            models.AdGroupSourceSettings.objects.filter(ad_group_source=self.ad_group_source).count() > 0
        )

        latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertEqual(latest_settings.state, 1)
        self.assertTrue(latest_settings.cpc_cc is None)
        self.assertTrue(latest_settings.daily_budget_cc is None)

    def test_should_write_if_changed(self):
        latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        request = HttpRequest()
        request.user = User(id=1)

        self.writer.set({'cpc_cc': decimal.Decimal(0.1)}, request)

        new_latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertNotEqual(new_latest_settings.id, latest_settings.id)
        self.assertEqual(float(new_latest_settings.cpc_cc), 0.1)
        self.assertNotEqual(new_latest_settings.cpc_cc, latest_settings.cpc_cc)
        self.assertEqual(new_latest_settings.state, latest_settings.state)
        self.assertEqual(new_latest_settings.daily_budget_cc, latest_settings.daily_budget_cc)

    def test_should_not_write_if_unchanged(self):
        latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        request = HttpRequest()

        self.writer.set({'daily_budget_cc': decimal.Decimal(50)}, request)

        new_latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertEqual(latest_settings.id, new_latest_settings.id)
        self.assertEqual(latest_settings.state, new_latest_settings.state)
        self.assertEqual(latest_settings.cpc_cc, new_latest_settings.cpc_cc)
        self.assertEqual(latest_settings.daily_budget_cc, new_latest_settings.daily_budget_cc)


class AdGroupSettingsOrderTest(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        self.ad_group_source = models.AdGroupSource.objects.get(id=1)

    def test_settings_changes(self):

        set1 = models.AdGroupSettings(
            created_dt=datetime.date.today(),

            state=1,
            start_date=datetime.date.today(),
            end_date=datetime.date.today(),
            cpc_cc=decimal.Decimal('0.1'),
            daily_budget_cc=decimal.Decimal('50.'),
        )

        set2 = models.AdGroupSettings(
            created_dt=datetime.date.today() - datetime.timedelta(days=1),

            state=2,
            start_date=datetime.date.today(),
            end_date=datetime.date.today(),
            cpc_cc=decimal.Decimal('0.2'),
            daily_budget_cc=decimal.Decimal('50.'),
        )

        self.assertEqual(set1.get_setting_changes(set1), {})

        self.assertEqual(
            set1.get_setting_changes(set2),
            {'state': 2, 'cpc_cc': decimal.Decimal('0.2')},
        )


class SubmitAdGroupCallbackTest(TestCase):

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

    def test_wrong_submission_type(self):
        ad_group_id = 1
        source_id = 1

        ad_group_source = models.AdGroupSource.objects.get(
            ad_group_id=ad_group_id,
            source_id=source_id,
        )

        with self.assertRaises(Exception):
            api.submit_ad_group_callback(ad_group_source, None, None, None)

    def test_approved(self):
        batch = models.UploadBatch.objects.create(name='test', status=constants.UploadBatchStatus.DONE)
        ad_group_id = 1
        source_id = 7

        ad_group_source = models.AdGroupSource.objects.get(
            ad_group_id=ad_group_id,
            source_id=source_id,
        )

        ad_group_source.source_content_ad_id = None
        ad_group_source.submission_status = constants.ContentAdSubmissionStatus.PENDING
        ad_group_source.submission_errors = None
        ad_group_source.save(None)

        content_ad1 = models.ContentAd.objects.create(
            url='test.com',
            title='test',
            ad_group=ad_group_source.ad_group,
            batch=batch
        )

        content_ad2 = models.ContentAd.objects.create(
            url='test.com',
            title='test',
            ad_group=ad_group_source.ad_group,
            batch=batch
        )

        content_ad3 = models.ContentAd.objects.create(
            url='test.com',
            title='test',
            ad_group=ad_group_source.ad_group,
            batch=batch
        )

        content_ad_source1 = models.ContentAdSource.objects.create(
            content_ad=content_ad1,
            source=ad_group_source.source,
            submission_status=constants.ContentAdSubmissionStatus.NOT_SUBMITTED,
            source_content_ad_id=None,
            state=constants.ContentAdSourceState.ACTIVE,
        )

        content_ad_source2 = models.ContentAdSource.objects.create(
            content_ad=content_ad2,
            source=ad_group_source.source,
            source_content_ad_id=None,
            submission_status=constants.ContentAdSubmissionStatus.REJECTED,
            state=constants.ContentAdSourceState.ACTIVE,
            submission_errors='test'
        )

        content_ad_source3 = models.ContentAdSource.objects.create(
            content_ad=content_ad3,
            source=ad_group_source.source,
            source_content_ad_id='987654321',
            submission_status=constants.ContentAdSubmissionStatus.PENDING,
            state=constants.ContentAdSourceState.ACTIVE,
            submission_errors=''
        )

        api.submit_ad_group_callback(
            ad_group_source,
            '1234567890',
            constants.ContentAdSubmissionStatus.APPROVED,
            None
        )

        ad_group_source = models.AdGroupSource.objects.get(id=ad_group_source.id)
        self.assertEqual(ad_group_source.source_content_ad_id, '1234567890')
        self.assertEqual(ad_group_source.submission_status, constants.ContentAdSubmissionStatus.APPROVED)
        self.assertEqual(ad_group_source.submission_errors, None)

        content_ad_source1 = models.ContentAdSource.objects.get(id=content_ad_source1.id)
        self.assertEqual(content_ad_source1.source_content_ad_id, '1234567890')
        self.assertEqual(content_ad_source1.submission_status, constants.ContentAdSubmissionStatus.APPROVED)
        self.assertEqual(content_ad_source1.submission_errors, None)

        content_ad_source2 = models.ContentAdSource.objects.get(id=content_ad_source2.id)
        self.assertEqual(content_ad_source2.source_content_ad_id, None)
        self.assertEqual(content_ad_source2.submission_status, constants.ContentAdSubmissionStatus.REJECTED)
        self.assertEqual(content_ad_source2.submission_errors, 'test')

        content_ad_source3 = models.ContentAdSource.objects.get(id=content_ad_source3.id)
        self.assertEqual(content_ad_source3.source_content_ad_id, '987654321')
        self.assertEqual(content_ad_source3.submission_status, constants.ContentAdSubmissionStatus.PENDING)
        self.assertEqual(content_ad_source3.submission_errors, '')

        insert_actionlogs1 = actionlog.models.ActionLog.objects.filter(
            content_ad_source=content_ad_source1,
            action=actionlog.constants.Action.INSERT_CONTENT_AD,
        )
        self.assertEqual(insert_actionlogs1.count(), 1)

        self.assertEqual(insert_actionlogs1[0].payload['args']['content_ad_id'], content_ad_source1.get_source_id())
        self.assertEqual(insert_actionlogs1[0].payload['args']['content_ad']['source_content_ad_id'], '1234567890')
        self.assertEqual(
            insert_actionlogs1[0].payload['args']['content_ad']['state'],
            constants.ContentAdSourceState.ACTIVE
        )

        insert_actionlogs2 = actionlog.models.ActionLog.objects.filter(
            content_ad_source=content_ad_source2,
            action=actionlog.constants.Action.INSERT_CONTENT_AD,
        )
        self.assertEqual(insert_actionlogs2.count(), 0)

        insert_actionlogs3 = actionlog.models.ActionLog.objects.filter(
            content_ad_source=content_ad_source3,
            action=actionlog.constants.Action.INSERT_CONTENT_AD,
        )
        self.assertEqual(insert_actionlogs3.count(), 0)

    def test_rejected(self):
        batch = models.UploadBatch.objects.create(name='test', status=constants.UploadBatchStatus.DONE)
        ad_group_id = 1
        source_id = 7

        ad_group_source = models.AdGroupSource.objects.get(
            ad_group_id=ad_group_id,
            source_id=source_id,
        )

        ad_group_source.source_content_ad_id = None
        ad_group_source.submission_status = constants.ContentAdSubmissionStatus.PENDING
        ad_group_source.submission_errors = None
        ad_group_source.save(None)

        content_ad = models.ContentAd.objects.create(
            url='test.com',
            title='test',
            ad_group=ad_group_source.ad_group,
            batch=batch
        )

        content_ad_source = models.ContentAdSource.objects.create(
            content_ad=content_ad,
            source=ad_group_source.source,
            submission_status=constants.ContentAdSubmissionStatus.NOT_SUBMITTED,
            state=constants.ContentAdSourceState.ACTIVE,
            source_state=None,
        )

        api.submit_ad_group_callback(
            ad_group_source,
            None,
            constants.ContentAdSubmissionStatus.REJECTED,
            'test'
        )

        self.assertEqual(ad_group_source.source_content_ad_id, None)
        self.assertEqual(ad_group_source.submission_status, constants.ContentAdSubmissionStatus.REJECTED)
        self.assertEqual(ad_group_source.submission_errors, 'test')

        content_ad_source = models.ContentAdSource.objects.get(id=content_ad_source.id)
        self.assertEqual(content_ad_source.source_content_ad_id, None)
        self.assertEqual(content_ad_source.submission_status, constants.ContentAdSubmissionStatus.REJECTED)
        self.assertEqual(content_ad_source.submission_errors, None)
        self.assertEqual(content_ad_source.state, constants.ContentAdSourceState.ACTIVE)
        self.assertEqual(content_ad_source.source_state, None)

        insert_actionlogs = actionlog.models.ActionLog.objects.filter(
            content_ad_source=content_ad_source,
            action=actionlog.constants.Action.INSERT_CONTENT_AD,
        )
        self.assertEqual(insert_actionlogs.count(), 1)

        self.assertEqual(insert_actionlogs[0].payload['args']['content_ad_id'], content_ad_source.get_source_id())
        self.assertEqual(
            insert_actionlogs[0].payload['args']['content_ad']['state'],
            constants.ContentAdSourceState.ACTIVE
        )

    def test_limit_reached(self):
        batch = models.UploadBatch.objects.create(name='test', status=constants.UploadBatchStatus.DONE)
        ad_group_id = 1
        source_id = 7

        ad_group_source = models.AdGroupSource.objects.get(
            ad_group_id=ad_group_id,
            source_id=source_id,
        )

        ad_group_source.source_content_ad_id = None
        ad_group_source.submission_status = constants.ContentAdSubmissionStatus.PENDING
        ad_group_source.submission_errors = None
        ad_group_source.save(None)

        content_ad = models.ContentAd.objects.create(
            url='test.com',
            title='test',
            ad_group=ad_group_source.ad_group,
            batch=batch
        )

        content_ad_source = models.ContentAdSource.objects.create(
            content_ad=content_ad,
            source=ad_group_source.source,
            submission_status=constants.ContentAdSubmissionStatus.NOT_SUBMITTED,
            state=constants.ContentAdSourceState.ACTIVE,
            source_state=None,
        )

        api.submit_ad_group_callback(
            ad_group_source,
            None,
            constants.ContentAdSubmissionStatus.LIMIT_REACHED,
            None
        )

        self.assertEqual(ad_group_source.source_content_ad_id, None)
        self.assertEqual(ad_group_source.submission_status, constants.ContentAdSubmissionStatus.LIMIT_REACHED)
        self.assertEqual(ad_group_source.submission_errors, None)

        content_ad_source = models.ContentAdSource.objects.get(id=content_ad_source.id)
        self.assertEqual(content_ad_source.source_content_ad_id, None)
        self.assertEqual(content_ad_source.submission_status, constants.ContentAdSubmissionStatus.NOT_SUBMITTED)
        self.assertEqual(content_ad_source.submission_errors, None)

        insert_actionlogs = actionlog.models.ActionLog.objects.filter(
            content_ad_source=content_ad_source,
            action=actionlog.constants.Action.INSERT_CONTENT_AD,
        )
        self.assertEqual(insert_actionlogs.count(), 0)


class SubmitContentAdsBatchTest(TestCase):

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

    def test_not_submitted_ad_group_source(self):
        batch = models.UploadBatch.objects.create(name='test', status=constants.UploadBatchStatus.DONE)
        ad_group_id = 1
        source_id = 7

        ad_group_source = models.AdGroupSource.objects.get(
            ad_group_id=ad_group_id,
            source_id=source_id,
        )

        ad_group_source.submission_status = constants.ContentAdSubmissionStatus.NOT_SUBMITTED
        ad_group_source.save(None)

        content_ad = models.ContentAd.objects.create(
            url='test.com',
            title='test',
            ad_group=ad_group_source.ad_group,
            batch=batch
        )

        content_ad_source = models.ContentAdSource.objects.create(
            content_ad=content_ad,
            source=ad_group_source.source,
        )

        api.submit_content_ads_batch(ad_group_id, batch, request=None)

        insert_actionlogs = actionlog.models.ActionLog.objects.filter(
            content_ad_source=content_ad_source,
            action=actionlog.constants.Action.INSERT_CONTENT_AD,
        )
        self.assertFalse(insert_actionlogs.exists())

        submit_actionlogs = actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action=actionlog.constants.Action.SUBMIT_AD_GROUP
        )
        self.assertEqual(submit_actionlogs.count(), 1)

    def test_not_submitted_ad_group_source_with_waiting_actionlog(self):
        batch = models.UploadBatch.objects.create(name='test', status=constants.UploadBatchStatus.DONE)
        ad_group_id = 1
        source_id = 7

        ad_group_source = models.AdGroupSource.objects.get(
            ad_group_id=ad_group_id,
            source_id=source_id,
        )

        ad_group_source.submission_status = constants.ContentAdSubmissionStatus.NOT_SUBMITTED
        ad_group_source.save(None)

        content_ad = models.ContentAd.objects.create(
            url='test.com',
            title='test',
            ad_group=ad_group_source.ad_group,
            batch=batch
        )

        content_ad_source = models.ContentAdSource.objects.create(
            content_ad=content_ad,
            source=ad_group_source.source,
        )

        actionlog.models.ActionLog.objects.create(
            action=actionlog.constants.Action.SUBMIT_AD_GROUP,
            state=actionlog.constants.ActionState.WAITING,
            action_type=actionlog.constants.ActionType.AUTOMATIC,
            ad_group_source=ad_group_source,
        )

        api.submit_content_ads_batch(ad_group_id, batch, request=None)

        insert_actionlogs = actionlog.models.ActionLog.objects.filter(
            content_ad_source=content_ad_source,
            action=actionlog.constants.Action.INSERT_CONTENT_AD,
        )
        self.assertFalse(insert_actionlogs.exists())

        submit_actionlogs = actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action=actionlog.constants.Action.SUBMIT_AD_GROUP
        )
        self.assertEquals(submit_actionlogs.count(), 1)

    def test_two_ad_group_sources(self):
        batch = models.UploadBatch.objects.create(name='test', status=constants.UploadBatchStatus.DONE)
        ad_group_id = 1
        source_id1 = 7
        source_id2 = 1

        ad_group_source1 = models.AdGroupSource.objects.get(
            ad_group_id=ad_group_id,
            source_id=source_id1,
        )

        ad_group_source1.submission_status = constants.ContentAdSubmissionStatus.NOT_SUBMITTED
        ad_group_source1.save(None)

        ad_group_source2 = models.AdGroupSource.objects.get(
            ad_group_id=ad_group_id,
            source_id=source_id2,
        )

        content_ad1 = models.ContentAd.objects.create(
            url='test.com',
            title='test',
            ad_group=ad_group_source1.ad_group,
            batch=batch
        )

        content_ad_source1 = models.ContentAdSource.objects.create(
            content_ad=content_ad1,
            source=ad_group_source1.source,
        )

        content_ad2 = models.ContentAd.objects.create(
            url='test.com',
            title='test',
            ad_group=ad_group_source2.ad_group,
            batch=batch
        )

        content_ad_source2 = models.ContentAdSource.objects.create(
            content_ad=content_ad2,
            source=ad_group_source2.source,
        )

        api.submit_content_ads_batch(ad_group_id, batch, request=None)

        insert_actionlogs1 = actionlog.models.ActionLog.objects.filter(
            content_ad_source=content_ad_source1,
            action=actionlog.constants.Action.INSERT_CONTENT_AD,
        )
        self.assertFalse(insert_actionlogs1.exists())

        submit_actionlogs1 = actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source1,
            action=actionlog.constants.Action.SUBMIT_AD_GROUP
        )
        self.assertEqual(submit_actionlogs1.count(), 1)

        insert_actionlogs2 = actionlog.models.ActionLog.objects.filter(
            content_ad_source=content_ad_source2,
            action=actionlog.constants.Action.INSERT_CONTENT_AD,
        )
        self.assertEqual(insert_actionlogs2.count(), 1)

        submit_actionlogs2 = actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source2,
            action=actionlog.constants.Action.SUBMIT_AD_GROUP
        )
        self.assertFalse(submit_actionlogs2.exists())

    def test_not_submitted_no_content_ads(self):
        batch = models.UploadBatch.objects.create(name='test', status=constants.UploadBatchStatus.DONE)
        ad_group_id = 1
        source_id = 7

        ad_group_source = models.AdGroupSource.objects.get(
            ad_group_id=ad_group_id,
            source_id=source_id,
        )

        ad_group_source.submission_status = constants.ContentAdSubmissionStatus.NOT_SUBMITTED
        ad_group_source.save(None)

        api.submit_content_ads_batch(ad_group_id, batch, request=None)

        insert_actionlogs = actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action=actionlog.constants.Action.INSERT_CONTENT_AD,
        )
        self.assertFalse(insert_actionlogs.exists())

        submit_actionlogs = actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action=actionlog.constants.Action.SUBMIT_AD_GROUP
        )
        self.assertFalse(submit_actionlogs.exists())

    def test_default_submission_type_source(self):
        batch = models.UploadBatch.objects.create(name='test', status=constants.UploadBatchStatus.DONE)
        ad_group_id = 1
        source_id = 1

        ad_group_source = models.AdGroupSource.objects.get(
            ad_group_id=ad_group_id,
            source_id=source_id,
        )

        content_ad = models.ContentAd.objects.create(
            url='test.com',
            title='test',
            ad_group=ad_group_source.ad_group,
            batch=batch
        )

        content_ad_source = models.ContentAdSource.objects.create(
            content_ad=content_ad,
            source=ad_group_source.source,
        )

        api.submit_content_ads_batch(ad_group_id, batch, request=None)

        insert_actionlogs = actionlog.models.ActionLog.objects.filter(
            content_ad_source=content_ad_source,
            action=actionlog.constants.Action.INSERT_CONTENT_AD,
        )
        self.assertEqual(insert_actionlogs.count(), 1)

        submit_actionlogs = actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action=actionlog.constants.Action.SUBMIT_AD_GROUP
        )
        self.assertFalse(submit_actionlogs.exists())

    def test_pending_ad_group_source(self):
        batch = models.UploadBatch.objects.create(name='test', status=constants.UploadBatchStatus.DONE)
        ad_group_id = 1
        source_id = 7

        ad_group_source = models.AdGroupSource.objects.get(
            ad_group_id=ad_group_id,
            source_id=source_id,
        )

        ad_group_source.submission_status = constants.ContentAdSubmissionStatus.PENDING
        ad_group_source.save(None)

        content_ad = models.ContentAd.objects.create(
            url='test.com',
            title='test',
            ad_group=ad_group_source.ad_group,
            batch=batch
        )

        content_ad_source = models.ContentAdSource.objects.create(
            content_ad=content_ad,
            source=ad_group_source.source,
        )

        api.submit_content_ads_batch(ad_group_id, batch, request=None)

        insert_actionlogs = actionlog.models.ActionLog.objects.filter(
            content_ad_source=content_ad_source,
            action=actionlog.constants.Action.INSERT_CONTENT_AD,
        )
        self.assertEqual(insert_actionlogs.count(), 1)

        submit_actionlogs = actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action=actionlog.constants.Action.SUBMIT_AD_GROUP
        )
        self.assertFalse(submit_actionlogs.exists())

    def test_limit_reached_ad_group_source(self):
        batch = models.UploadBatch.objects.create(name='test', status=constants.UploadBatchStatus.DONE)
        ad_group_id = 1
        source_id = 7

        ad_group_source = models.AdGroupSource.objects.get(
            ad_group_id=ad_group_id,
            source_id=source_id,
        )

        ad_group_source.submission_status = constants.ContentAdSubmissionStatus.LIMIT_REACHED
        ad_group_source.save(None)

        content_ad = models.ContentAd.objects.create(
            url='test.com',
            title='test',
            ad_group=ad_group_source.ad_group,
            batch=batch
        )

        content_ad_source = models.ContentAdSource.objects.create(
            content_ad=content_ad,
            source=ad_group_source.source,
        )

        api.submit_content_ads_batch(ad_group_id, batch, request=None)

        insert_actionlogs = actionlog.models.ActionLog.objects.filter(
            content_ad_source=content_ad_source,
            action=actionlog.constants.Action.INSERT_CONTENT_AD,
        )
        self.assertFalse(insert_actionlogs.exists())

        submit_actionlogs = actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action=actionlog.constants.Action.SUBMIT_AD_GROUP
        )
        self.assertFalse(submit_actionlogs.exists())
