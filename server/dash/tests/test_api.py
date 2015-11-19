import decimal
import datetime
import mock

from django.conf import settings
from django.test import TestCase, TransactionTestCase, override_settings
from django.http.request import HttpRequest

import actionlog.constants
import actionlog.models

import dash.models

from dash import models
from dash import api
from dash import constants

from zemauth.models import User

from utils import test_helper


class AddContentAdSources(TestCase):
    fixtures = ['test_api.yaml']

    def setUp(self):
        self.request = HttpRequest()
        self.request.user = User.objects.create_user('test@example.com')

    def test_ad_content_ad_sources_supported(self):
        ad_group_source = models.AdGroupSource(
            source_id=5,
            ad_group_id=1,
        )
        ad_group_source.can_manage_content_ads = True
        ad_group_source.save(self.request)

        content_ad_sources = api.add_content_ad_sources(ad_group_source)

        expected = [
            models.ContentAdSource.objects.create(
                source_id=5,
                content_ad_id=1,
                submission_status=constants.ContentAdSubmissionStatus.NOT_SUBMITTED,
                state=constants.ContentAdSourceState.ACTIVE
            ),
            models.ContentAdSource.objects.create(
                source_id=5,
                content_ad_id=2,
                submission_status=constants.ContentAdSubmissionStatus.NOT_SUBMITTED,
                state=constants.ContentAdSourceState.INACTIVE
            ),
            models.ContentAdSource.objects.create(
                source_id=5,
                content_ad_id=3,
                submission_status=constants.ContentAdSubmissionStatus.NOT_SUBMITTED,
                state=constants.ContentAdSourceState.INACTIVE
            )
        ]

        self.assertEqual(len(content_ad_sources), 3)
        content_ad_sources.sort(key=lambda x: x.content_ad_id)

        for content_ad_source, expected_object in zip(content_ad_sources, expected):
            self.assertEqual(content_ad_source.source_id, expected_object.source_id)
            self.assertEqual(content_ad_source.content_ad_id, expected_object.content_ad_id)
            self.assertEqual(content_ad_source.submission_status, expected_object.submission_status)
            self.assertEqual(content_ad_source.state, expected_object.state)

    def test_ad_content_ad_sources_not_supported(self):
        ad_group_source = models.AdGroupSource(
            source_id=4,
            ad_group_id=1,
        )
        ad_group_source.save(self.request)

        content_ad_sources = api.add_content_ad_sources(ad_group_source)

        self.assertEqual(content_ad_sources, [])


class UpdateContentAdSourceState(TestCase):
    fixtures = ['test_api.yaml']

    def test_update_multiple_content_ad_source_states(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        content_ad_data = [{
            'id': 1,
            'state': 2,
            'submission_status': constants.ContentAdSubmissionStatus.APPROVED
        }]

        content_ad_source = models.ContentAdSource.objects.get(pk=1)
        content_ad_source.content_ad.state = 2
        content_ad_source.content_ad.save()

        api.update_multiple_content_ad_source_states(ad_group_source, content_ad_data)

        content_ad_source = models.ContentAdSource.objects.get(pk=1)

        self.assertEqual(content_ad_source.source_state, content_ad_data[0]['state'])
        self.assertEqual(content_ad_source.submission_status, content_ad_data[0]['submission_status'])

    def test_update_multiple_content_ad_source_ids(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        content_ad_data = [{
            'id': 1,
            'state': 2,
            'submission_status': constants.ContentAdSubmissionStatus.APPROVED,
            'source_content_ad_id': 'asd123'
        }]

        api.update_multiple_content_ad_source_states(ad_group_source, content_ad_data)

        content_ad_source = models.ContentAdSource.objects.get(pk=1)

        self.assertEqual(content_ad_source.source_content_ad_id, content_ad_data[0]['source_content_ad_id'])

    def test_update_content_ad_source_state(self):
        content_ad_source = models.ContentAdSource.objects.get(pk=1)
        data = {'source_state': 2, 'submission_status': 2}

        api.update_content_ad_source_state(content_ad_source, data)

        content_ad_source = models.ContentAdSource.objects.get(pk=1)
        self.assertEqual(content_ad_source.source_state, data['source_state'])
        self.assertEqual(content_ad_source.submission_status, data['submission_status'])


class IgnorePendingContentAdSourceSubmissionWhenLocalStatusIsRejected(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        # create reference to an Outbrain AdGroupSource
        source = models.Source.objects.get(source_type__type=constants.SourceType.OUTBRAIN)
        self.ad_group_source = models.AdGroupSource.objects.filter(source=source).first()

        # create ContentAd
        batch = models.UploadBatch.objects.create(name='test', status=constants.UploadBatchStatus.DONE)

        content_ad = models.ContentAd.objects.create(
            url='test.com',
            title='test',
            ad_group=self.ad_group_source.ad_group,
            batch=batch
        )

        # create ContentAdSource
        self.content_ad_source = models.ContentAdSource.objects.create(
            content_ad=content_ad,
            source=self.ad_group_source.source,
            submission_status=constants.ContentAdSubmissionStatus.REJECTED,
            source_content_ad_id=None,
            state=constants.ContentAdSourceState.ACTIVE,
        )

    def test_update_content_ad_source_state(self):
        # create an incoming data object containing the submission_status PENDING
        content_ad_data = {'submission_status': constants.ContentAdSubmissionStatus.PENDING}

        # pass the objects to update_content_ad_source_state
        api.update_content_ad_source_state(self.content_ad_source, content_ad_data)

        # refresh the ContentAdSource and assert the status is still REJECTED
        self.content_ad_source.refresh_from_db()
        self.assertEqual(self.content_ad_source.submission_status, constants.ContentAdSubmissionStatus.REJECTED)

    def test_update_multiple_content_ad_source_states(self):
        # create an incoming data object containing the submission_status PENDING
        content_ad_data = [{'id': self.content_ad_source.get_source_id(),
                            'state': self.content_ad_source.source_state,
                            'submission_status': constants.ContentAdSubmissionStatus.PENDING}]

        # ensure our ContentAdSource is found by the filter, otherwise the test will PASS without testing anything
        self.assertTrue(self.content_ad_source in models.ContentAdSource.objects.filter(
                content_ad__ad_group=self.ad_group_source.ad_group,
                source=self.ad_group_source.source))

        # pass the AdGroupSource and incoming data to update_multiple_content_ad_source_states
        api.update_multiple_content_ad_source_states(self.ad_group_source, content_ad_data)

        # refresh the ContentAdSource and assert the status is still REJECTED
        self.content_ad_source.refresh_from_db()
        self.assertEqual(self.content_ad_source.submission_status, constants.ContentAdSubmissionStatus.REJECTED)


class AutomaticallyApproveContentAdSourceSubmissionStatus(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        self.content_ad_source = models.ContentAdSource.objects.get(id=1)
        self.content_ad_source.submission_status = constants.ContentAdSubmissionStatus.LIMIT_REACHED
        self.content_ad_source.source_content_ad_id = 'test'
        self.content_ad_source.save()

        account = self.content_ad_source.content_ad.ad_group.campaign.account
        account.outbrain_marketer_id = api.AUTOMATIC_APPROVAL_OUTBRAIN_ACCOUNT

        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

        account.save(request)

        self.content_ad_source.source.source_type = models.SourceType.objects.get(type=constants.SourceType.OUTBRAIN)
        self.content_ad_source.source.save()

    def test_update_content_ad_source_state_auto_approved(self):
        content_ad_data = {'submission_status': constants.ContentAdSubmissionStatus.PENDING}

        api.update_content_ad_source_state(self.content_ad_source, content_ad_data)

        self.content_ad_source.refresh_from_db()
        self.assertEqual(self.content_ad_source.submission_status, constants.ContentAdSubmissionStatus.APPROVED)

    def test_update_multiple_content_ad_source_states_auto_approved(self):
        content_ad_data = [{'id': 'test', 'state': 2, 'submission_status': constants.ContentAdSubmissionStatus.PENDING}]

        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        api.update_multiple_content_ad_source_states(ad_group_source, content_ad_data)

        self.content_ad_source.refresh_from_db()
        self.assertEqual(self.content_ad_source.submission_status, constants.ContentAdSubmissionStatus.APPROVED)

    def test_insert_content_ad_callback(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        api.insert_content_ad_callback(ad_group_source, self.content_ad_source, None, None,
                                       constants.ContentAdSubmissionStatus.PENDING, None)

        self.content_ad_source.refresh_from_db()
        self.assertEqual(self.content_ad_source.submission_status, constants.ContentAdSubmissionStatus.APPROVED)


@override_settings(
    R1_REDIRECTS_ADGROUP_API_URL='https://r1.example.com/api/redirects/',
    R1_API_SIGN_KEY='AAAAAAAAAAAAAAAAAAAAAAAA'
)
class UpdateAdGroupSourceSettings(TestCase):
    fixtures = ['test_api.yaml']

    def setUp(self):
        self.props = []
        self.values = []

        patcher = mock.patch('utils.redirector_helper.insert_adgroup')
        self.mock_insert_adgroup = patcher.start()
        self.addCleanup(patcher.stop)

    def _get_manual_set_property_actions(self, ad_group_source):
        return actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action_type=actionlog.constants.ActionType.MANUAL,
            action=actionlog.constants.Action.SET_PROPERTY
        )

    def _get_automatic_set_campaign_state_actions(self, ad_group_source):
        return actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action_type=actionlog.constants.ActionType.AUTOMATIC,
            action=actionlog.constants.Action.SET_CAMPAIGN_STATE
        )

    def _get_automatic_action_conf(self, action_log):
        return action_log.payload['args']['conf']

    def test_ad_group_name_change(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.append(
            constants.SourceAction.CAN_MODIFY_AD_GROUP_NAME
        )
        ad_group_source.source.source_type.save()
        ad_group_source.save()

        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.ad_group_name = "Test"

        api.order_ad_group_settings_update(ad_group_source.ad_group, adgs1, adgs2, None)
        auto_actions = self._get_automatic_set_campaign_state_actions(ad_group_source)
        self.assertEqual(1, len(auto_actions))
        self.assertTrue('name' in self._get_automatic_action_conf(auto_actions[0]))
        self.assertTrue(self.mock_insert_adgroup.called, 'Should be called because settings are fresh')

    def test_basic_manual_actions(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.maintenance = True
        ad_group_source.save()

        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.ad_group_name = "Test"

        ret = api.order_ad_group_settings_update(ad_group_source.ad_group, adgs1, adgs2, None)
        self.assertEqual([], ret)
        self.assertTrue(self.mock_insert_adgroup.called, 'Should be called because settings are fresh')

    @mock.patch('dash.api.actionlog.api')
    def test_tracking_code_manual_action(self, mock_api):
        ad_group_source = models.AdGroupSource.objects.get(id=16)

        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.tracking_code = "test={amazing}&blob={sourceDomain}&x={sourceDomainUnderscore}"

        ret = api.order_ad_group_settings_update(ad_group_source.ad_group, adgs1, adgs2, None)
        self.assertEqual([], ret)

        expected_value = 'test={amazing}' +\
            '&blob={slug}&x={slug}&_z1_adgid=7&_z1_msid={slug}'.format(slug=ad_group_source.source.tracking_slug)

        mock_api.init_set_ad_group_manual_property.assert_called_with(
            mock.ANY, None, 'tracking_code', expected_value)

        self.assertTrue(self.mock_insert_adgroup.called)
        self.assertEqual(self.mock_insert_adgroup.call_args[0][0], ad_group_source.ad_group_id)
        self.assertEqual(self.mock_insert_adgroup.call_args[0][1], adgs2.tracking_code)

    def test_tracking_codes_automatic(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.append(
            constants.SourceAction.CAN_MODIFY_TRACKING_CODES
        )
        ad_group_source.source.source_type.save()

        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.tracking_code = "a=b"

        ret = api.order_ad_group_settings_update(ad_group_source.ad_group, adgs1, adgs2, None)
        self.assertEqual(2, len(ret))
        self.assertEqual(ret[0].action, actionlog.constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(ret[1].action, actionlog.constants.Action.SET_CAMPAIGN_STATE)

        self.assertTrue(self.mock_insert_adgroup.called)
        self.assertEqual(self.mock_insert_adgroup.call_args[0][0], ad_group_source.ad_group_id)
        self.assertEqual(self.mock_insert_adgroup.call_args[0][1], adgs2.tracking_code)

    def test_tracking_codes_automatic_per_content_ad(self):
        ad_group_source1 = models.AdGroupSource.objects.get(id=1)
        ad_group_source1.can_manage_content_ads = True
        ad_group_source1.save()

        ad_group_source1.source.source_type.available_actions.append(
            constants.SourceAction.UPDATE_TRACKING_CODES_ON_CONTENT_ADS
        )
        ad_group_source1.source.source_type.available_actions.append(
            constants.SourceAction.CAN_MODIFY_TRACKING_CODES
        )
        ad_group_source1.source.source_type.save()

        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.tracking_code = "a=b"

        ret = api.order_ad_group_settings_update(ad_group_source1.ad_group, adgs1, adgs2, None)
        self.assertEqual(1, len(ret))
        self.assertEqual(ret[0].action, actionlog.constants.Action.UPDATE_CONTENT_AD)

        self.assertTrue(self.mock_insert_adgroup.called)
        self.assertEqual(self.mock_insert_adgroup.call_args[0][0], ad_group_source1.ad_group_id)
        self.assertEqual(self.mock_insert_adgroup.call_args[0][1], adgs2.tracking_code)

    def test_target_regions_automatic_action(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.append(
            constants.SourceAction.CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_AUTOMATIC,
        )
        ad_group_source.source.source_type.available_actions.append(
            constants.SourceAction.CAN_MODIFY_COUNTRY_TARGETING
        )
        ad_group_source.source.source_type.save()

        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.target_regions = ['GB', '693', 'US-AL']

        api.order_ad_group_settings_update(
            ad_group_source.ad_group, adgs1, adgs2, None, iab_update=True)

        auto_actions = self._get_automatic_set_campaign_state_actions(ad_group_source)
        self.assertEqual(1, len(auto_actions))
        self.assertDictEqual(self._get_automatic_action_conf(auto_actions[0]), {
            'target_regions': ['GB', '693', 'US-AL']
        })

        man_actions = self._get_manual_set_property_actions(ad_group_source)
        self.assertFalse(man_actions.exists())

    def test_target_regions_automatic_country_and_manual_dma_action(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.append(
            constants.SourceAction.CAN_MODIFY_COUNTRY_TARGETING
        )
        ad_group_source.source.source_type.available_actions.append(
            constants.SourceAction.CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_MANUAL
        )
        ad_group_source.source.source_type.save()

        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.target_regions = ['GB', '693']

        api.order_ad_group_settings_update(
            ad_group_source.ad_group, adgs1, adgs2, None, iab_update=True)

        auto_actions = self._get_automatic_set_campaign_state_actions(ad_group_source)
        self.assertEqual(0, len(auto_actions))

        man_actions = self._get_manual_set_property_actions(ad_group_source)
        self.assertEqual(1, len(man_actions))
        self.assertDictEqual(man_actions[0].payload, {
            'property': 'target_regions',
            'value': {
                'countries': ['GB'],
                'dma': ['693 Little Rock-Pine Bluff, AR']
            }
        })

    def test_target_regions_automatic_country_and_manual_subdivision_action(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.append(
            constants.SourceAction.CAN_MODIFY_COUNTRY_TARGETING
        )
        ad_group_source.source.source_type.available_actions.append(
            constants.SourceAction.CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_MANUAL
        )
        ad_group_source.source.source_type.save()

        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.target_regions = ['GB', 'US-AL']

        api.order_ad_group_settings_update(
            ad_group_source.ad_group, adgs1, adgs2, None, iab_update=True)

        auto_actions = self._get_automatic_set_campaign_state_actions(ad_group_source)
        self.assertEqual(0, len(auto_actions))

        man_actions = self._get_manual_set_property_actions(ad_group_source)
        self.assertEqual(1, len(man_actions))
        self.assertDictEqual(man_actions[0].payload, {
            'property': 'target_regions',
            'value': {
                'countries': ['GB'],
                'subdivisions': ['Alabama']
            }
        })

    def test_target_regions_no_dma_action(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)

        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.target_regions = ['694', '693']

        api.order_ad_group_settings_update(
            ad_group_source.ad_group, adgs1, adgs2, None, iab_update=True)

        auto_actions = self._get_automatic_set_campaign_state_actions(ad_group_source)
        self.assertEqual(0, len(auto_actions))

        man_actions = self._get_manual_set_property_actions(ad_group_source)
        self.assertEqual(0, len(man_actions))

    def test_target_regions_no_subdivision_action(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)

        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.target_regions = ['US-AL', 'US-OK']

        api.order_ad_group_settings_update(
            ad_group_source.ad_group, adgs1, adgs2, None, iab_update=True)

        auto_actions = self._get_automatic_set_campaign_state_actions(ad_group_source)
        self.assertEqual(0, len(auto_actions))

        man_actions = self._get_manual_set_property_actions(ad_group_source)
        self.assertEqual(0, len(man_actions))

    def test_target_regions_manual_country_and_automatic_dma_action(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.append(
            constants.SourceAction.CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_AUTOMATIC
        )
        ad_group_source.source.source_type.save()

        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.target_regions = ['GB', '693']

        api.order_ad_group_settings_update(
            ad_group_source.ad_group, adgs1, adgs2, None, iab_update=True)

        auto_actions = self._get_automatic_set_campaign_state_actions(ad_group_source)
        self.assertEqual(0, len(auto_actions))

        man_actions = self._get_manual_set_property_actions(ad_group_source)
        self.assertEqual(1, len(man_actions))
        self.assertDictEqual(man_actions[0].payload, {
            'property': 'target_regions', 'value': {
                'countries': ['GB'],
                'dma': ['693 Little Rock-Pine Bluff, AR']
            }})

    def test_target_regions_manual_country_and_automatic_subdivision_action(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.append(
            constants.SourceAction.CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_AUTOMATIC
        )
        ad_group_source.source.source_type.save()

        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.target_regions = ['GB', 'US-AL']

        api.order_ad_group_settings_update(
            ad_group_source.ad_group, adgs1, adgs2, None, iab_update=True)

        auto_actions = self._get_automatic_set_campaign_state_actions(ad_group_source)
        self.assertEqual(0, len(auto_actions))

        man_actions = self._get_manual_set_property_actions(ad_group_source)
        self.assertEqual(1, len(man_actions))
        self.assertDictEqual(man_actions[0].payload, {
            'property': 'target_regions', 'value': {
                'countries': ['GB'],
                'subdivisions': ['Alabama']
            }})

    def test_target_regions_manual_country_and_manual_dma_action(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.append(
            constants.SourceAction.CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_MANUAL
        )
        ad_group_source.source.source_type.save()

        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.target_regions = ['GB', '693']

        api.order_ad_group_settings_update(
            ad_group_source.ad_group, adgs1, adgs2, None, iab_update=True)

        auto_actions = self._get_automatic_set_campaign_state_actions(ad_group_source)
        self.assertEqual(0, len(auto_actions))

        man_actions = self._get_manual_set_property_actions(ad_group_source)
        self.assertEqual(1, len(man_actions))
        self.assertDictEqual(man_actions[0].payload, {
            'property': 'target_regions',
            'value': {
                'countries': ['GB'],
                'dma': ['693 Little Rock-Pine Bluff, AR']
            }
        })

    def test_target_regions_manual_country_and_manual_subdivision_action(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.append(
            constants.SourceAction.CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_MANUAL
        )
        ad_group_source.source.source_type.save()

        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.target_regions = ['GB', 'US-AL']

        api.order_ad_group_settings_update(
            ad_group_source.ad_group, adgs1, adgs2, None, iab_update=True)

        auto_actions = self._get_automatic_set_campaign_state_actions(ad_group_source)
        self.assertEqual(0, len(auto_actions))

        man_actions = self._get_manual_set_property_actions(ad_group_source)
        self.assertEqual(1, len(man_actions))
        self.assertDictEqual(man_actions[0].payload, {
            'property': 'target_regions',
            'value': {
                'countries': ['GB'],
                'subdivisions': ['Alabama']
            }
        })

    def test_target_regions_manual_dma_targeting_cleared(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.append(
            constants.SourceAction.CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_MANUAL
        )
        ad_group_source.source.source_type.save()

        adgs1 = models.AdGroupSettings()
        adgs1.target_regions = ['GB', '693']
        adgs2 = models.AdGroupSettings()
        adgs2.target_regions = ['GB']

        api.order_ad_group_settings_update(
            ad_group_source.ad_group, adgs1, adgs2, None, iab_update=True)

        auto_actions = self._get_automatic_set_campaign_state_actions(ad_group_source)
        self.assertEqual(0, len(auto_actions))

        man_actions = self._get_manual_set_property_actions(ad_group_source)
        self.assertEqual(1, len(man_actions))
        self.assertDictEqual(man_actions[0].payload, {
            'property': 'target_regions',
            'value': {
                'dma': 'cleared (no DMA targeting)',
                'countries': ['GB']
            }})

    def test_target_regions_manual_subdivision_targeting_cleared(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.append(
            constants.SourceAction.CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_MANUAL
        )
        ad_group_source.source.source_type.save()

        adgs1 = models.AdGroupSettings()
        adgs1.target_regions = ['GB', 'US-AL']
        adgs2 = models.AdGroupSettings()
        adgs2.target_regions = ['GB']

        api.order_ad_group_settings_update(
            ad_group_source.ad_group, adgs1, adgs2, None, iab_update=True)

        auto_actions = self._get_automatic_set_campaign_state_actions(ad_group_source)
        self.assertEqual(0, len(auto_actions))

        man_actions = self._get_manual_set_property_actions(ad_group_source)
        self.assertEqual(1, len(man_actions))
        self.assertDictEqual(man_actions[0].payload, {
            'property': 'target_regions',
            'value': {
                'subdivisions': 'cleared (no subdivision targeting)',
                'countries': ['GB']
            }})

    def test_target_regions_manual_dma_manual_country_target_worldwide(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.append(
            constants.SourceAction.CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_MANUAL
        )
        ad_group_source.source.source_type.save()

        adgs1 = models.AdGroupSettings()
        adgs1.target_regions = ['GB', '693']
        adgs2 = models.AdGroupSettings()
        adgs2.target_regions = []

        api.order_ad_group_settings_update(
            ad_group_source.ad_group, adgs1, adgs2, None, iab_update=True)

        auto_actions = self._get_automatic_set_campaign_state_actions(ad_group_source)
        self.assertEqual(0, len(auto_actions))

        man_actions = self._get_manual_set_property_actions(ad_group_source)
        self.assertEqual(1, len(man_actions))
        self.assertDictEqual(man_actions[0].payload, {
            'property': 'target_regions',
            'value': {
                'countries': 'Worldwide',
                'dma': 'cleared (no DMA targeting)'
            }
        })

    def test_target_regions_manual_subdivision_manual_country_target_worldwide(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.append(
            constants.SourceAction.CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_MANUAL
        )
        ad_group_source.source.source_type.save()

        adgs1 = models.AdGroupSettings()
        adgs1.target_regions = ['GB', 'US-AL']
        adgs2 = models.AdGroupSettings()
        adgs2.target_regions = []

        api.order_ad_group_settings_update(
            ad_group_source.ad_group, adgs1, adgs2, None, iab_update=True)

        auto_actions = self._get_automatic_set_campaign_state_actions(ad_group_source)
        self.assertEqual(0, len(auto_actions))

        man_actions = self._get_manual_set_property_actions(ad_group_source)
        self.assertEqual(1, len(man_actions))
        self.assertDictEqual(man_actions[0].payload, {
            'property': 'target_regions',
            'value': {
                'countries': 'Worldwide',
                'subdivisions': 'cleared (no subdivision targeting)'
            }
        })

    def test_target_regions_automatic_dma_manual_country_target_worldwide(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.append(
            constants.SourceAction.CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_AUTOMATIC
        )
        ad_group_source.source.source_type.save()

        adgs1 = models.AdGroupSettings()
        adgs1.target_regions = ['GB', '693']
        adgs2 = models.AdGroupSettings()
        adgs2.target_regions = []

        api.order_ad_group_settings_update(
            ad_group_source.ad_group, adgs1, adgs2, None, iab_update=True)

        auto_actions = self._get_automatic_set_campaign_state_actions(ad_group_source)
        self.assertEqual(0, len(auto_actions))

        man_actions = self._get_manual_set_property_actions(ad_group_source)
        self.assertEqual(1, len(man_actions))
        self.assertDictEqual(man_actions[0].payload, {
            'property': 'target_regions',
            'value': {
                'countries': 'Worldwide',
                'dma': 'cleared (no DMA targeting)'
            }
        })

    def test_target_regions_automatic_subdivision_manual_country_target_worldwide(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.append(
            constants.SourceAction.CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_AUTOMATIC
        )
        ad_group_source.source.source_type.save()

        adgs1 = models.AdGroupSettings()
        adgs1.target_regions = ['GB', 'US-AL']
        adgs2 = models.AdGroupSettings()
        adgs2.target_regions = []

        api.order_ad_group_settings_update(
            ad_group_source.ad_group, adgs1, adgs2, None, iab_update=True)

        auto_actions = self._get_automatic_set_campaign_state_actions(ad_group_source)
        self.assertEqual(0, len(auto_actions))

        man_actions = self._get_manual_set_property_actions(ad_group_source)
        self.assertEqual(1, len(man_actions))
        self.assertDictEqual(man_actions[0].payload, {
            'property': 'target_regions',
            'value': {
                'countries': 'Worldwide',
                'subdivisions': 'cleared (no subdivision targeting)'
            }
        })

    def test_target_regions_all_manual(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.append(
            constants.SourceAction.CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_MANUAL
        )
        ad_group_source.source.source_type.save()

        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.target_regions = ['NL', 'US-OK', '693']

        api.order_ad_group_settings_update(
            ad_group_source.ad_group, adgs1, adgs2, None, iab_update=True)

        auto_actions = self._get_automatic_set_campaign_state_actions(ad_group_source)
        self.assertEqual(0, len(auto_actions))

        man_actions = self._get_manual_set_property_actions(ad_group_source)
        self.assertEqual(1, len(man_actions))
        self.assertDictEqual(man_actions[0].payload, {
            'property': 'target_regions',
            'value': {
                'countries': ['NL'],
                'subdivisions': ['Oklahoma'],
                'dma': ['693 Little Rock-Pine Bluff, AR']
            }
        })

    def test_tracking_codes_automatic_action_for_gravity(self):
        """ Tests a fix for a bug in gravitys dashboard - when a tracking code does not
        have a value assigned, it should create a manual action, even though the source
        is set to create an automatic action for tracking code changes.

        This test tests if the automatic action is created.
        """

        ad_group_source = models.AdGroupSource.objects.get(id=2)
        ad_group_source.source.source_type.available_actions.append(
            constants.SourceAction.CAN_MODIFY_TRACKING_CODES
        )
        ad_group_source.source.source_type.save()

        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.tracking_code = 'test=123'

        api.order_ad_group_settings_update(
            ad_group_source.ad_group, adgs1, adgs2, None, iab_update=True)

        # should have an automatic action
        automatic_actions = actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action_type=actionlog.constants.ActionType.AUTOMATIC,
            action=actionlog.constants.Action.SET_CAMPAIGN_STATE
        )
        manual_actions = actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action_type=actionlog.constants.ActionType.MANUAL,
            action=actionlog.constants.Action.SET_CAMPAIGN_STATE
        )
        self.assertEqual(1, len(automatic_actions))
        self.assertEqual(0, len(manual_actions))
        self.assertIn('tracking_code', automatic_actions[0].payload['args']['conf'])

    def test_tracking_codes_manual_action_for_gravity(self):
        """ Tests a fix for a bug in gravitys dashboard - when a tracking code does not
        have a value assigned, it should create a manual action, even though the source
        is set to create an automatic action for tracking code changes.

        This test tests if the manual action is created.
        """

        ad_group_source = models.AdGroupSource.objects.get(id=2)  # should be Gravity
        ad_group_source.source.source_type.available_actions.append(
            constants.SourceAction.CAN_MODIFY_TRACKING_CODES
        )
        ad_group_source.source.source_type.save()

        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.tracking_code = 'test'

        api.order_ad_group_settings_update(
            ad_group_source.ad_group, adgs1, adgs2, None, iab_update=True)

        # should have an automatic action
        automatic_actions = actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action_type=actionlog.constants.ActionType.AUTOMATIC,
            action=actionlog.constants.Action.SET_CAMPAIGN_STATE
        )
        manual_actions = actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action_type=actionlog.constants.ActionType.MANUAL,
            action=actionlog.constants.Action.SET_PROPERTY,
        )
        self.assertEqual(0, len(automatic_actions))
        self.assertEqual(1, len(manual_actions))
        self.assertEqual('tracking_code', manual_actions[0].payload['property'])

    def test_iab_category_manual(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.append(
            constants.SourceAction.CAN_MODIFY_AD_GROUP_IAB_CATEGORY_MANUAL
        )
        ad_group_source.source.source_type.save()

        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.iab_category = 'IAB1'

        manual_actions = actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action_type=actionlog.constants.ActionType.MANUAL
        )

        self.assertFalse(manual_actions.exists())

        ret = api.order_ad_group_settings_update(
            ad_group_source.ad_group, adgs1, adgs2, None, iab_update=True)

        self.assertEqual([], ret)
        self.assertTrue(manual_actions.exists())

    def test_iab_category_automatic(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.append(
            constants.SourceAction.CAN_MODIFY_AD_GROUP_IAB_CATEGORY_AUTOMATIC
        )
        ad_group_source.source.source_type.save()

        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.iab_category = 'IAB1'

        ret = api.order_ad_group_settings_update(
            ad_group_source.ad_group, adgs1, adgs2, None, iab_update=True)

        self.assertEqual(2, len(ret))
        for r in ret:
            self.assertEqual(r.action, actionlog.constants.Action.SET_CAMPAIGN_STATE)
            self.assertEqual(r.action_type, actionlog.constants.ActionType.AUTOMATIC)

    def test_iab_category_none(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.iab_category = 'IAB1'

        manual_actions = actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action_type=actionlog.constants.ActionType.MANUAL
        )

        self.assertFalse(manual_actions.exists())

        ret = api.order_ad_group_settings_update(
            ad_group_source.ad_group, adgs1, adgs2, None, iab_update=True)

        self.assertEqual([], ret)
        self.assertFalse(manual_actions.exists())

    def test_tracking_propagation_remove_tracking_ids(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.append(
            constants.SourceAction.CAN_MODIFY_TRACKING_CODES
        )
        ad_group_source.source.source_type.save()

        adgs1 = models.AdGroupSettings()
        adgs1.enable_adobe_tracking = True
        adgs1.adobe_tracking_param = 'cid'
        adgs2 = models.AdGroupSettings()
        adgs2.enable_ga_tracking = False
        adgs2.enable_adobe_tracking = False
        adgs2.adobe_tracking_param = ''

        api.order_ad_group_settings_update(ad_group_source.ad_group, adgs1, adgs2, None)
        self.mock_insert_adgroup.assert_called_with(1, '', False, False, '')

        manual_actions = self._get_manual_set_property_actions(ad_group_source)
        auto_actions = self._get_automatic_set_campaign_state_actions(ad_group_source)

        self.assertFalse(manual_actions.exists())
        self.assertEqual(len(auto_actions), 1)

        # should create automatic action with tracking code change - remove tracking ids
        self.assertDictEqual(
            self._get_automatic_action_conf(auto_actions[0]),
            {
                'tracking_code': ''
            }
        )

    def test_tracking_propagation_add_tracking_ids(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.append(
            constants.SourceAction.CAN_MODIFY_TRACKING_CODES
        )
        ad_group_source.source.source_type.save()

        adgs1 = models.AdGroupSettings()
        adgs1.enable_ga_tracking = False
        adgs1.enable_adobe_tracking = False
        adgs1.adobe_tracking_param = ''
        adgs2 = models.AdGroupSettings()
        adgs2.enable_ga_tracking = True
        adgs2.enable_adobe_tracking = True
        adgs2.adobe_tracking_param = 'cid'

        api.order_ad_group_settings_update(ad_group_source.ad_group, adgs1, adgs2, None)
        self.mock_insert_adgroup.assert_called_with(1, '', True, True, 'cid')

        manual_actions = self._get_manual_set_property_actions(ad_group_source)
        auto_actions = self._get_automatic_set_campaign_state_actions(ad_group_source)

        self.assertFalse(manual_actions.exists())
        self.assertEqual(len(auto_actions), 1)

        # should create automatic action with tracking code change - add tracking ids
        self.assertDictEqual(
            self._get_automatic_action_conf(auto_actions[0]),
            {
                'tracking_code': '_z1_adgid=1&_z1_msid={sourceDomain}'
            }
        )

    def test_propagate_redirects(self):
        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()

        api.order_ad_group_settings_update(models.AdGroup.objects.get(pk=1), adgs1, adgs2, None)

        # should insert ad group into redirector as settings are fresh
        self.mock_insert_adgroup.assert_called_with(1, '', True, False, '')

    def test_no_need_to_propagate_redirects(self):
        adgs1 = models.AdGroupSettings(ad_group_id=1)
        adgs1.save(None)

        adgs2 = models.AdGroupSettings()

        api.order_ad_group_settings_update(models.AdGroup.objects.get(pk=1), adgs1, adgs2, None)
        # no need to insert into redirector - settings exist from before, no changes
        self.assertFalse(self.mock_insert_adgroup.called)

    def test_changes_propagate_redirects(self):
        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings(tracking_code='asd')

        api.order_ad_group_settings_update(models.AdGroup.objects.get(pk=1), adgs1, adgs2, None)
        # should insert ad group into redirector as relevant settings were changed
        self.mock_insert_adgroup.assert_called_with(1, 'asd', True, False, '')


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


class PublisherCallbackTest(TransactionTestCase):
    fixtures = ['test_api.yaml']

    def test_update_publisher_blacklist(self):

        ad_group_source = models.AdGroupSource.objects.get(id=1)

        args = {
            'key': [1],
            'level': dash.constants.PublisherBlacklistLevel.ADGROUP,
            'state': dash.constants.PublisherStatus.BLACKLISTED,
            'publishers': [{
                'domain': 'zemanta.com',
                'exchange': 'adiant',
                'source_id': 7
            },
            {
                'domain': 'test1.com',
                'exchange': 'sharethrough',
                'source_id': 9
            }]
        }

        api.update_publisher_blacklist_state(args)
        allblacklist = dash.models.PublisherBlacklist.objects.all()
        self.assertEqual(2, allblacklist.count())

        first_blacklist = allblacklist[0]
        self.assertEqual(ad_group_source.ad_group.id, first_blacklist.ad_group.id)
        self.assertEqual('zemanta.com', first_blacklist.name)
        self.assertEqual('b1_adiant', first_blacklist.source.tracking_slug)
        self.assertEqual(dash.constants.PublisherStatus.BLACKLISTED, first_blacklist.status)

        second_blacklist = allblacklist[1]
        self.assertEqual(ad_group_source.ad_group.id, second_blacklist.ad_group.id)
        self.assertEqual('b1_sharethrough', second_blacklist.source.tracking_slug)
        self.assertEqual(dash.constants.PublisherStatus.BLACKLISTED, second_blacklist.status)


    def test_hiearchy_publisher_blacklist(self):
        ad_group = models.AdGroup.objects.get(pk=1)
        adiant = models.Source.objects.get(tracking_slug='b1_adiant')
        sharethrough = models.Source.objects.get(tracking_slug='b1_sharethrough')
        models.PublisherBlacklist.objects.create(
            name='zemanta.com',
            ad_group=ad_group,
            source=adiant,
            status=dash.constants.PublisherStatus.BLACKLISTED
        )

        models.PublisherBlacklist.objects.create(
            name='test1.com',
            ad_group=ad_group,
            source=sharethrough,
            status=dash.constants.PublisherStatus.BLACKLISTED
        )

        args = {
            'key': [1],
            'level': dash.constants.PublisherBlacklistLevel.ADGROUP,
            'state': dash.constants.PublisherStatus.ENABLED,
            'publishers': [{
                'domain': 'zemanta.com',
                'exchange': 'adiant',
                'source_id': 7,
            },
            {
                'domain': 'test1.com',
                'exchange': 'sharethrough',
                'source_id': 9,
            }]
        }

        api.update_publisher_blacklist_state(args)
        allblacklist = dash.models.PublisherBlacklist.objects.all()
        self.assertEqual(0, allblacklist.count())


    def test_hiearchy_publisher_blacklist_wo_delete(self):
        # if we get a request to blacklist per adgroup source
        # and we already have a blacklist per campaign source,
        # account source or globally nothing happens
        ad_group = models.AdGroup.objects.get(pk=1)
        adiant = models.Source.objects.get(tracking_slug='b1_adiant')
        sharethrough = models.Source.objects.get(tracking_slug='b1_sharethrough')
        models.PublisherBlacklist.objects.create(
            name='zemanta.com',
            campaign=ad_group.campaign,
            source=adiant,
            status=dash.constants.PublisherStatus.BLACKLISTED
        )

        models.PublisherBlacklist.objects.create(
            name='test1.com',
            campaign=ad_group.campaign,
            source=sharethrough,
            status=dash.constants.PublisherStatus.BLACKLISTED
        )

        args = {
            'key': [1],
            'level': dash.constants.PublisherBlacklistLevel.ADGROUP,
            'state': dash.constants.PublisherStatus.ENABLED,
            'publishers': [{
                'domain': 'zemanta.com',
                'exchange': 'adiant',
                'source_id': 7,
            },
            {
                'domain': 'test1.com',
                'exchange': 'sharethrough',
                'source_id': 9,
            }]
        }

        api.update_publisher_blacklist_state(args)
        allblacklist = dash.models.PublisherBlacklist.objects.all()
        self.assertEqual(2, allblacklist.count())

        self.assertTrue(all([blacklist.campaign is not None
                             for blacklist in allblacklist]))

    def test_hiearchy_publisher_blacklist_plus_one(self):
        # blacklisting on higher level overrides lower level blacklist
        # adgroup < campaign < account < global
        ad_group = models.AdGroup.objects.get(pk=1)
        adiant = models.Source.objects.get(tracking_slug='b1_adiant')
        models.PublisherBlacklist.objects.create(
            name='zemanta.com',
            ad_group=ad_group,
            source=adiant,
            status=dash.constants.PublisherStatus.BLACKLISTED
        )

        args = {
            'key': [1],
            'level': dash.constants.PublisherBlacklistLevel.ADGROUP,
            'state': dash.constants.PublisherStatus.BLACKLISTED,
            'publishers': [{
                'domain': 'zemanta.com',
                'exchange': 'adiant',
                'source_id': 7
            }]
        }

        api.update_publisher_blacklist_state(args)
        allblacklist = dash.models.PublisherBlacklist.objects.all()
        self.assertEqual(1, allblacklist.count())
        self.assertIsNotNone(allblacklist[0].ad_group)


        args1 = {
            'key': [1],
            'level': dash.constants.PublisherBlacklistLevel.CAMPAIGN,
            'state': dash.constants.PublisherStatus.BLACKLISTED,
            'publishers': [{
                'domain': 'zemanta.com',
                'exchange': 'adiant',
                'source_id': 7
            }]
        }

        api.update_publisher_blacklist_state(args1)
        allblacklist = dash.models.PublisherBlacklist.objects.all()
        self.assertEqual(1, allblacklist.count())
        self.assertIsNone(allblacklist[0].ad_group)
        self.assertIsNotNone(allblacklist[0].campaign)


        args2 = {
            'key': [1],
            'level': dash.constants.PublisherBlacklistLevel.ACCOUNT,
            'state': dash.constants.PublisherStatus.BLACKLISTED,
            'publishers': [{
                'domain': 'zemanta.com',
                'exchange': 'adiant',
                'source_id': 7
            }]
        }

        api.update_publisher_blacklist_state(args2)
        allblacklist = dash.models.PublisherBlacklist.objects.all()
        self.assertEqual(1, allblacklist.count())
        self.assertIsNone(allblacklist[0].ad_group)
        self.assertIsNone(allblacklist[0].campaign)
        self.assertIsNotNone(allblacklist[0].account)


        args3 = {
            'key': None,
            'level': dash.constants.PublisherBlacklistLevel.GLOBAL,
            'state': dash.constants.PublisherStatus.BLACKLISTED,
            'publishers': [{
                'domain': 'zemanta.com',
                'exchange': 'adiant',
                'source_id': 7
            }]
        }

        api.update_publisher_blacklist_state(args3)
        allblacklist = dash.models.PublisherBlacklist.objects.all()
        self.assertEqual(1, allblacklist.count())
        self.assertIsNone(allblacklist[0].ad_group)
        self.assertIsNone(allblacklist[0].campaign)
        self.assertIsNone(allblacklist[0].account)
        self.assertTrue(allblacklist[0].everywhere)

    def test_refresh_publisher_blacklist_rtb(self):
        # blacklisting on higher level overrides lower level blacklist
        # adgroup < campaign < account < global
        ad_group = models.AdGroup.objects.get(pk=1)
        adiant = models.Source.objects.get(tracking_slug='b1_adiant')
        models.PublisherBlacklist.objects.create(
            name='zemanta.com',
            campaign=ad_group.campaign,
            source=adiant,
            status=dash.constants.PublisherStatus.BLACKLISTED
        )

        adgs = dash.models.AdGroupSource.objects.filter(
            ad_group=ad_group,
            source=adiant
        ).first()
        api.refresh_publisher_blacklist(adgs, None)

        actions = actionlog.models.ActionLog.objects.all()
        self.assertEqual(1, actions.count())


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
        request.user = User.objects.create_user('test@example.com')

        self.ad_group_settings.state = 1
        self.ad_group_settings.save(request)
        self.assertTrue(self.writer.can_trigger_action())

    @mock.patch('actionlog.api.utils.email_helper.send_ad_group_notification_email')
    @mock.patch('actionlog.api.set_ad_group_source_settings')
    def test_should_write_if_no_settings_yet(self, set_ad_group_source_settings, mock_send_mail):
        self.assertTrue(
            models.AdGroupSourceSettings.objects.filter(ad_group_source=self.ad_group_source).count() > 0
        )
        # delete all ad_group_source_settings
        models.AdGroupSourceSettings.objects.filter(ad_group_source=self.ad_group_source).delete()

        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

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
        self.assertFalse(set_ad_group_source_settings.called)

        mock_send_mail.assert_called_with(self.ad_group_source.ad_group, request)

    @mock.patch('actionlog.api.utils.email_helper.send_ad_group_notification_email')
    @mock.patch('actionlog.api.set_ad_group_source_settings')
    def test_should_write_if_changed(self, set_ad_group_source_settings, mock_send_mail):
        latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

        self.writer.set({'cpc_cc': decimal.Decimal(0.1)}, request)

        new_latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertNotEqual(new_latest_settings.id, latest_settings.id)
        self.assertEqual(float(new_latest_settings.cpc_cc), 0.1)
        self.assertNotEqual(new_latest_settings.cpc_cc, latest_settings.cpc_cc)
        self.assertEqual(new_latest_settings.state, latest_settings.state)
        self.assertEqual(new_latest_settings.daily_budget_cc, latest_settings.daily_budget_cc)
        self.assertTrue(set_ad_group_source_settings.called)

        mock_send_mail.assert_called_with(self.ad_group_source.ad_group, request)

    @mock.patch('actionlog.api.utils.email_helper.send_ad_group_notification_email')
    @mock.patch('actionlog.api.set_ad_group_source_settings')
    def test_should_write_if_request_none(self, set_ad_group_source_settings, mock_send_mail):
        latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        request = None

        self.writer.set({'cpc_cc': decimal.Decimal(0.1)}, request)

        new_latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertNotEqual(new_latest_settings.id, latest_settings.id)
        self.assertEqual(float(new_latest_settings.cpc_cc), 0.1)
        self.assertNotEqual(new_latest_settings.cpc_cc, latest_settings.cpc_cc)
        self.assertEqual(new_latest_settings.state, latest_settings.state)
        self.assertEqual(new_latest_settings.daily_budget_cc, latest_settings.daily_budget_cc)
        self.assertTrue(set_ad_group_source_settings.called)

        self.assertFalse(mock_send_mail.called)

    @mock.patch('actionlog.api.utils.email_helper.send_ad_group_notification_email')
    @mock.patch('actionlog.api.set_ad_group_source_settings')
    def test_should_write_if_changed_no_action(self, set_ad_group_source_settings, mock_send_mail):
        latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

        self.writer.set({'cpc_cc': decimal.Decimal(0.1)}, request, send_action=False)

        new_latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertNotEqual(new_latest_settings.id, latest_settings.id)
        self.assertEqual(float(new_latest_settings.cpc_cc), 0.1)
        self.assertNotEqual(new_latest_settings.cpc_cc, latest_settings.cpc_cc)
        self.assertEqual(new_latest_settings.state, latest_settings.state)
        self.assertEqual(new_latest_settings.daily_budget_cc, latest_settings.daily_budget_cc)
        self.assertFalse(set_ad_group_source_settings.called)

        mock_send_mail.assert_called_with(self.ad_group_source.ad_group, request)

    @mock.patch('actionlog.api.utils.email_helper.send_ad_group_notification_email')
    @mock.patch('actionlog.api.set_ad_group_source_settings')
    def test_should_not_write_if_unchanged(self, set_ad_group_source_settings, mock_send_mail):
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
        self.assertFalse(set_ad_group_source_settings.called)

        self.assertFalse(mock_send_mail.called)


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

        self.assertEqual(insert_actionlogs1[0].payload['args']['content_ad']['content_ad_id'], content_ad_source1.get_source_id())
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

        self.assertEqual(insert_actionlogs[0].payload['args']['content_ad']['content_ad_id'], content_ad_source.get_source_id())
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


class UpdateContentAdSubmissionStatus(TestCase):

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

    def test_ad_group_submission_type(self):
        batch = models.UploadBatch.objects.create(name='test', status=constants.UploadBatchStatus.DONE)
        ad_group_id = 1
        source_id = 7

        ad_group_source = models.AdGroupSource.objects.get(
            ad_group_id=ad_group_id,
            source_id=source_id,
        )

        ad_group_source.submission_status = constants.ContentAdSubmissionStatus.APPROVED
        ad_group_source.source_content_ad_id = '987654321'
        ad_group_source.save(None)

        content_ad = models.ContentAd.objects.create(
            url='test.com',
            title='test',
            ad_group=ad_group_source.ad_group,
            batch=batch
        )

        content_ad_source1 = models.ContentAdSource.objects.create(
            content_ad=content_ad,
            source=ad_group_source.source,
            submission_status=constants.ContentAdSubmissionStatus.PENDING,
            source_content_ad_id='1234567890',
        )

        content_ad_source2 = models.ContentAdSource.objects.create(
            content_ad=content_ad,
            source=ad_group_source.source,
            submission_status=constants.ContentAdSubmissionStatus.REJECTED,
            source_content_ad_id=None,
        )

        api.update_content_ads_submission_status(ad_group_source, request=None)

        content_ad_source1 = models.ContentAdSource.objects.get(id=content_ad_source1.id)
        self.assertEqual(content_ad_source1.submission_status, constants.ContentAdSubmissionStatus.APPROVED)
        self.assertEqual(content_ad_source1.source_content_ad_id, '987654321')

        content_ad_source2 = models.ContentAdSource.objects.get(id=content_ad_source2.id)
        self.assertEqual(content_ad_source2.submission_status, constants.ContentAdSubmissionStatus.REJECTED)
        self.assertEqual(content_ad_source2.source_content_ad_id, None)

        update_actionlogs = actionlog.models.ActionLog.objects.filter(
            content_ad_source=content_ad_source1,
            action=actionlog.constants.Action.UPDATE_CONTENT_AD,
        )
        self.assertEqual(update_actionlogs.count(), 1)

    def test_default_submission_type(self):
        batch = models.UploadBatch.objects.create(name='test', status=constants.UploadBatchStatus.DONE)
        ad_group_id = 1
        source_id = 1

        ad_group_source = models.AdGroupSource.objects.get(
            ad_group_id=ad_group_id,
            source_id=source_id,
        )

        ad_group_source.submission_status = constants.ContentAdSubmissionStatus.REJECTED
        ad_group_source.source_content_ad_id = None
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
            submission_status=constants.ContentAdSubmissionStatus.APPROVED,
            source_content_ad_id='1234567890',
        )

        api.update_content_ads_submission_status(ad_group_source, request=None)

        content_ad_source = models.ContentAdSource.objects.get(id=content_ad_source.id)
        self.assertEqual(content_ad_source.submission_status, constants.ContentAdSubmissionStatus.APPROVED)
        self.assertEqual(content_ad_source.source_content_ad_id, '1234567890')

        update_actionlogs = actionlog.models.ActionLog.objects.filter(
            content_ad_source=content_ad_source,
            action=actionlog.constants.Action.UPDATE_CONTENT_AD,
        )
        self.assertFalse(update_actionlogs.exists())


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

    def test_submission_type_batch(self):
        batch1 = models.UploadBatch.objects.create(name='test1', status=constants.UploadBatchStatus.DONE)
        batch2 = models.UploadBatch.objects.create(name='test2', status=constants.UploadBatchStatus.DONE)

        ad_group_id = 1
        source_id = 8

        ad_group_source = models.AdGroupSource.objects.create(
            ad_group_id=ad_group_id,
            source_id=source_id,
            source_campaign_key='fake_key',
            source_credentials_id=1
        )
        ad_group_source.save(None)

        content_ad1 = models.ContentAd.objects.create(
            url='test1.com',
            title='test1',
            ad_group=ad_group_source.ad_group,
            batch=batch1
        )
        content_ad_source1 = models.ContentAdSource.objects.create(
            content_ad=content_ad1,
            source=ad_group_source.source,
        )

        content_ad2 = models.ContentAd.objects.create(
            url='test2.com',
            title='test2',
            ad_group=ad_group_source.ad_group,
            batch=batch2
        )
        content_ad_source2 = models.ContentAdSource.objects.create(
            content_ad=content_ad2,
            source=ad_group_source.source,
        )

        content_ad3 = models.ContentAd.objects.create(
            url='test3.com',
            title='test3',
            ad_group=ad_group_source.ad_group,
            batch=batch2
        )
        content_ad_source3 = models.ContentAdSource.objects.create(
            content_ad=content_ad3,
            source=ad_group_source.source,
        )

        api.submit_content_ads([content_ad_source1, content_ad_source2, content_ad_source3], request=None)

        actionlogs = actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action=actionlog.constants.Action.INSERT_CONTENT_AD_BATCH
        )
        self.assertEqual(actionlogs.count(), 2)

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

        api.submit_content_ads([content_ad_source], request=None)

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

        api.submit_content_ads([content_ad_source], request=None)

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

        api.submit_content_ads([content_ad_source1, content_ad_source2], request=None)

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
        ad_group_id = 1
        source_id = 7

        ad_group_source = models.AdGroupSource.objects.get(
            ad_group_id=ad_group_id,
            source_id=source_id,
        )

        ad_group_source.submission_status = constants.ContentAdSubmissionStatus.NOT_SUBMITTED
        ad_group_source.save(None)

        api.submit_content_ads([], request=None)

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

        api.submit_content_ads([content_ad_source], request=None)

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

        api.submit_content_ads([content_ad_source], request=None)

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

        api.submit_content_ads([content_ad_source], request=None)

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


class CreateCampaignAdditionalUpdatesCallbackTest(TestCase):
    fixtures = ['test_zwei_api.yaml']

    def setUp(self):
        password = 'secret'
        user = User.objects.get(pk=1)

        self.request = HttpRequest()
        self.request.user = user
        self.client.login(username=user.email, password=password)

    def _setup_ad_group(self, ad_group_source, target_regions=None, available_actions=None):
        if available_actions:
            ad_group_source.source.source_type.available_actions.extend(available_actions)
            ad_group_source.source.source_type.save()

        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        ad_group_settings.target_regions = target_regions
        ad_group_settings.save(self.request)

    def _get_created_manual_actions(self, ad_group_source):
        return actionlog.models.ActionLog.objects.filter(
            action=actionlog.constants.Action.SET_PROPERTY,
            ad_group_source=ad_group_source,
            action_type=actionlog.constants.ActionType.MANUAL
        )

    def _get_set_campaign_state_actions(self, ad_group_source):
        return actionlog.models.ActionLog.objects.filter(
            action=actionlog.constants.Action.SET_CAMPAIGN_STATE,
            ad_group_source=ad_group_source
        )

    def test_manual_update_after_campaign_creation_manual_dma_targeting(self):
        ad_group_source = models.AdGroupSource.objects.get(id=3)

        self._setup_ad_group(ad_group_source, ['GB', '693'], [
            constants.SourceAction.CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_MANUAL,
            constants.SourceAction.CAN_MODIFY_COUNTRY_TARGETING
        ])

        api.order_additional_updates_after_campaign_creation(ad_group_source, self.request)

        manual_actions = self._get_created_manual_actions(ad_group_source)

        # should create manual actions
        self.assertEqual(len(manual_actions), 1)
        self.assertEqual('target_regions', manual_actions[0].payload['property'])

    def test_no_manual_update_after_campaign_creation_auto_targeting(self):
        ad_group_source = models.AdGroupSource.objects.get(id=3)

        self._setup_ad_group(
            ad_group_source,
            ['GB', '693'],
            [
                constants.SourceAction.CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_AUTOMATIC,
                constants.SourceAction.CAN_MODIFY_COUNTRY_TARGETING
            ])

        api.order_additional_updates_after_campaign_creation(ad_group_source, self.request)

        manual_actions = self._get_created_manual_actions(ad_group_source)

        # should not create manual actions
        self.assertFalse(manual_actions.exists())

    def test_no_manual_update_after_campaign_creation_dma_targeting_not_supported(self):
        ad_group_source = models.AdGroupSource.objects.get(id=3)

        self._setup_ad_group(
            ad_group_source,
            ['GB', '693'],
            [constants.SourceAction.CAN_MODIFY_COUNTRY_TARGETING]
        )

        api.order_additional_updates_after_campaign_creation(ad_group_source, self.request)

        manual_actions = self._get_created_manual_actions(ad_group_source)

        # should not create manual actions
        self.assertFalse(manual_actions.exists())

    def test_no_manual_update_after_campaign_creation_no_dma_targeting(self):
        ad_group_source = models.AdGroupSource.objects.get(id=3)

        self._setup_ad_group(
            ad_group_source,
            ['GB'],
            [
                constants.SourceAction.CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_AUTOMATIC,
                constants.SourceAction.CAN_MODIFY_COUNTRY_TARGETING
            ])

        api.order_additional_updates_after_campaign_creation(ad_group_source, self.request)

        manual_actions = self._get_created_manual_actions(ad_group_source)

        # should not create manual actions
        self.assertFalse(manual_actions.exists())

    def test_source_settings_update_after_campaign_creation_no_action(self):
        ad_group_source = models.AdGroupSource.objects.get(id=5)

        api.order_additional_updates_after_campaign_creation(ad_group_source, self.request)

        self.assertFalse(self._get_set_campaign_state_actions(ad_group_source).exists())

    def test_source_settings_update_after_campaign_creation_create_action(self):
        ad_group_source = models.AdGroupSource.objects.get(id=3)

        api.order_additional_updates_after_campaign_creation(ad_group_source, self.request)

        actions = self._get_set_campaign_state_actions(ad_group_source)
        self.assertEqual(actions.count(), 1)
        self.assertDictEqual(actions.first().payload['args']['conf'], {
            'cpc_cc': 1200
        })
