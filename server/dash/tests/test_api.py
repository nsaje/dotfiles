import decimal
import datetime
import mock

from django.conf import settings
from django.test import TestCase, override_settings
from django.http.request import HttpRequest

import actionlog.constants
import actionlog.models
import actionlog.api

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

    @mock.patch('dash.api.redirector_helper.insert_adgroup')
    def test_ad_group_name_change(self, insert_adgroup_mock):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.add(
            models.SourceAction.objects.get(
                action=constants.SourceAction.CAN_MODIFY_AD_GROUP_NAME,
            )
        )
        ad_group_source.save()

        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.ad_group_name = "Test"

        ret = api.order_ad_group_settings_update(ad_group_source.ad_group, adgs1, adgs2, None)
        self.assertEqual(2, len(ret))
        self.assertEqual(ret[0].action, actionlog.constants.Action.SET_CAMPAIGN_STATE)
        self.assertTrue('name' in ret[0].payload['args']['conf'])

        self.assertEqual(ret[1].action, actionlog.constants.Action.SET_CAMPAIGN_STATE)
        self.assertTrue('name' in ret[1].payload['args']['conf'])
        self.assertFalse(insert_adgroup_mock.called)

    @mock.patch('dash.api.redirector_helper.insert_adgroup')
    def test_basic_manual_actions(self, insert_adgroup_mock):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.maintenance = True
        ad_group_source.save()

        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.ad_group_name = "Test"

        ret = api.order_ad_group_settings_update(ad_group_source.ad_group, adgs1, adgs2, None)
        self.assertEqual([], ret)
        self.assertFalse(insert_adgroup_mock.called)

    @mock.patch('dash.api.redirector_helper.insert_adgroup')
    @mock.patch('dash.api.actionlog.api')
    def test_tracking_code_manual_action(self, mock_api, insert_adgroup_mock):
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

        self.assertTrue(insert_adgroup_mock.called)
        self.assertEqual(insert_adgroup_mock.call_args[0][0], ad_group_source.ad_group_id)
        self.assertEqual(insert_adgroup_mock.call_args[0][1], adgs2.tracking_code)

    @mock.patch('dash.api.redirector_helper.insert_adgroup')
    def test_tracking_codes_automatic(self, insert_adgroup_mock):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.add(
            models.SourceAction.objects.get(
                action=constants.SourceAction.CAN_MODIFY_TRACKING_CODES,
            )
        )

        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.tracking_code = "a=b"

        ret = api.order_ad_group_settings_update(ad_group_source.ad_group, adgs1, adgs2, None)
        self.assertEqual(2, len(ret))
        self.assertEqual(ret[0].action, actionlog.constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(ret[1].action, actionlog.constants.Action.SET_CAMPAIGN_STATE)

        self.assertTrue(insert_adgroup_mock.called)
        self.assertEqual(insert_adgroup_mock.call_args[0][0], ad_group_source.ad_group_id)
        self.assertEqual(insert_adgroup_mock.call_args[0][1], adgs2.tracking_code)

    @mock.patch('dash.api.redirector_helper.insert_adgroup')
    def test_tracking_codes_automatic_per_content_ad(self, insert_adgroup_mock):
        ad_group_source1 = models.AdGroupSource.objects.get(id=1)
        ad_group_source1.can_manage_content_ads = True
        ad_group_source1.save()

        ad_group_source1.source.source_type.available_actions.add(
            models.SourceAction.objects.get(
                action=constants.SourceAction.UPDATE_TRACKING_CODES_ON_CONTENT_ADS,
            )
        )
        ad_group_source1.source.source_type.available_actions.add(
            models.SourceAction.objects.get(
                action=constants.SourceAction.CAN_MODIFY_TRACKING_CODES,
            )
        )

        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.tracking_code = "a=b"

        ret = api.order_ad_group_settings_update(ad_group_source1.ad_group, adgs1, adgs2, None)
        self.assertEqual(1, len(ret))
        self.assertEqual(ret[0].action, actionlog.constants.Action.UPDATE_CONTENT_AD)

        self.assertTrue(insert_adgroup_mock.called)
        self.assertEqual(insert_adgroup_mock.call_args[0][0], ad_group_source1.ad_group_id)
        self.assertEqual(insert_adgroup_mock.call_args[0][1], adgs2.tracking_code)

    def test_target_regions_automatic_action(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.add(
            models.SourceAction.objects.get(
                action=constants.SourceAction.CAN_MODIFY_DMA_TARGETING_AUTOMATIC
            )
        )
        ad_group_source.source.source_type.available_actions.add(
            models.SourceAction.objects.get(
                action=constants.SourceAction.CAN_MODIFY_COUNTRY_TARGETING
            )
        )

        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.target_regions = ['GB', '693']

        ret = api.order_ad_group_settings_update(
            ad_group_source.ad_group, adgs1, adgs2, None, iab_update=True)

        self.assertEqual(2, len(ret))
        for r in ret:
            self.assertEqual(r.action, actionlog.constants.Action.SET_CAMPAIGN_STATE)
            self.assertEqual(r.action_type, actionlog.constants.ActionType.AUTOMATIC)

        manual_actions = actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action_type=actionlog.constants.ActionType.MANUAL
        )
        self.assertFalse(manual_actions.exists())

    def test_target_regions_automatic_country_and_manual_dma_action(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.add(
            models.SourceAction.objects.get(
                action=constants.SourceAction.CAN_MODIFY_COUNTRY_TARGETING
            )
        )
        ad_group_source.source.source_type.available_actions.add(
            models.SourceAction.objects.get(
                action=constants.SourceAction.CAN_MODIFY_DMA_TARGETING_MANUAL
            )
        )

        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.target_regions = ['GB', '693']

        ret = api.order_ad_group_settings_update(
            ad_group_source.ad_group, adgs1, adgs2, None, iab_update=True)

        self.assertEqual(2, len(ret))
        for r in ret:
            self.assertEqual(r.action, actionlog.constants.Action.SET_CAMPAIGN_STATE)
            self.assertEqual(r.action_type, actionlog.constants.ActionType.AUTOMATIC)

        manual_actions = actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action_type=actionlog.constants.ActionType.MANUAL
        )
        self.assertEqual(len(manual_actions), 1)
        self.assertEqual(manual_actions[0].payload, {'property': 'target_regions_dma', 'value': ['693 Little Rock-Pine Bluff, AR', "countries: ['GB']"]})

    def test_target_regions_no_dma_action(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)

        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.target_regions = ['694', '693']

        ret = api.order_ad_group_settings_update(
            ad_group_source.ad_group, adgs1, adgs2, None, iab_update=True)

        self.assertEqual(0, len(ret))

        manual_actions = actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action_type=actionlog.constants.ActionType.MANUAL
        )
        self.assertEqual(len(manual_actions), 0)

    def test_target_regions_manual_country_and_automatic_dma_action(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.add(
            models.SourceAction.objects.get(
                action=constants.SourceAction.CAN_MODIFY_DMA_TARGETING_AUTOMATIC
            )
        )

        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.target_regions = ['GB', '693']

        ret = api.order_ad_group_settings_update(
            ad_group_source.ad_group, adgs1, adgs2, None, iab_update=True)

        self.assertEqual(2, len(ret))
        for r in ret:
            self.assertEqual(r.action, actionlog.constants.Action.SET_CAMPAIGN_STATE)
            self.assertEqual(r.action_type, actionlog.constants.ActionType.AUTOMATIC)

        manual_actions = actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action_type=actionlog.constants.ActionType.MANUAL
        )
        self.assertEqual(len(manual_actions), 1)
        self.assertEqual(manual_actions[0].payload, {'property': 'target_regions_countries', 'value': ['GB']})

    def test_target_regions_manual_country_and_manual_dma_action(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.add(
            models.SourceAction.objects.get(
                action=constants.SourceAction.CAN_MODIFY_DMA_TARGETING_MANUAL
            )
        )

        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.target_regions = ['GB', '693']

        ret = api.order_ad_group_settings_update(
            ad_group_source.ad_group, adgs1, adgs2, None, iab_update=True)

        self.assertEqual(0, len(ret))

        manual_actions = actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action_type=actionlog.constants.ActionType.MANUAL
        )
        self.assertItemsEqual([ma.payload for ma in manual_actions], [
            {'property': 'target_regions_countries', 'value': ['GB']},
            {'property': 'target_regions_dma', 'value': ['693 Little Rock-Pine Bluff, AR', "countries: ['GB']"]}
        ])

    def test_target_regions_manual_dma_targeting_cleared(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.add(
            models.SourceAction.objects.get(
                action=constants.SourceAction.CAN_MODIFY_DMA_TARGETING_MANUAL
            )
        )

        adgs1 = models.AdGroupSettings()
        adgs1.target_regions = ['GB', '693']
        adgs2 = models.AdGroupSettings()
        adgs2.target_regions = ['GB']

        ret = api.order_ad_group_settings_update(
            ad_group_source.ad_group, adgs1, adgs2, None, iab_update=True)

        self.assertEqual(0, len(ret))

        manual_actions = actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action_type=actionlog.constants.ActionType.MANUAL
        )
        self.assertEqual(len(manual_actions), 1)
        self.assertEqual(manual_actions[0].payload, {'property': 'target_regions_dma', 'value': ['cleared (no DMA targeting)', "countries: ['GB']"]})

    def test_target_regions_manual_dma_manual_country_target_worldwide(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.add(
            models.SourceAction.objects.get(
                action=constants.SourceAction.CAN_MODIFY_DMA_TARGETING_MANUAL
            )
        )

        adgs1 = models.AdGroupSettings()
        adgs1.target_regions = ['GB', '693']
        adgs2 = models.AdGroupSettings()
        adgs2.target_regions = []

        ret = api.order_ad_group_settings_update(
            ad_group_source.ad_group, adgs1, adgs2, None, iab_update=True)

        self.assertEqual(0, len(ret))

        manual_actions = actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action_type=actionlog.constants.ActionType.MANUAL
        )
        self.assertItemsEqual([ma.payload for ma in manual_actions], [
            {'property': 'target_regions_countries', 'value': 'Worldwide'},
            {'property': 'target_regions_dma', 'value': ['cleared (no DMA targeting)', "countries: Worldwide"]}
        ])

    def test_target_regions_automatic_dma_manual_country_target_worldwide(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.add(
            models.SourceAction.objects.get(
                action=constants.SourceAction.CAN_MODIFY_DMA_TARGETING_AUTOMATIC
            )
        )

        adgs1 = models.AdGroupSettings()
        adgs1.target_regions = ['GB', '693']
        adgs2 = models.AdGroupSettings()
        adgs2.target_regions = []

        ret = api.order_ad_group_settings_update(
            ad_group_source.ad_group, adgs1, adgs2, None, iab_update=True)

        self.assertEqual(2, len(ret))
        for r in ret:
            self.assertEqual(r.action, actionlog.constants.Action.SET_CAMPAIGN_STATE)
            self.assertEqual(r.action_type, actionlog.constants.ActionType.AUTOMATIC)

        manual_actions = actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action_type=actionlog.constants.ActionType.MANUAL
        )
        self.assertItemsEqual([ma.payload for ma in manual_actions], [
            {'property': 'target_regions_countries', 'value': 'Worldwide'},
        ])

    def test_iab_category_manual(self):
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.add(
            models.SourceAction.objects.get(
                action=constants.SourceAction.CAN_MODIFY_AD_GROUP_IAB_CATEGORY_MANUAL
            )
        )

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
        ad_group_source.source.source_type.available_actions.add(
            models.SourceAction.objects.get(
                action=constants.SourceAction.CAN_MODIFY_AD_GROUP_IAB_CATEGORY_AUTOMATIC
            )
        )

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

    @mock.patch('dash.api.redirector_helper.insert_adgroup')
    def test_ga_tracking_propagation(self, insert_adgroup_mock):
        ad_group_source1 = models.AdGroupSource.objects.get(id=1)

        adgs1 = models.AdGroupSettings()
        adgs2 = models.AdGroupSettings()
        adgs2.enable_ga_tracking = False  # the only change (default is True)

        ret = api.order_ad_group_settings_update(ad_group_source1.ad_group, adgs1, adgs2, None)
        insert_adgroup_mock.assert_called_with(1, '', disable_auto_tracking=True)

        manual_actions = actionlog.models.ActionLog.objects.filter(
            ad_group_source=ad_group_source1,
            action_type=actionlog.constants.ActionType.MANUAL
        )

        # no manual nor automatic actions created
        self.assertFalse(manual_actions.exists())
        self.assertEqual([], ret)


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
        request.user = User.objects.create_user('test@example.com')

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

    def test_should_write_if_changed(self):
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
