import datetime
from decimal import Decimal

from django import test

import core.entity
import dash.features.videoassets.models
import core.goals
import core.bcm
import dash.constants

from analytics import delivery, constants

from utils.magic_mixer import magic_mixer


class CampaignDeliveryTestCase(test.TestCase):

    def setUp(self):
        self.account = magic_mixer.blend(core.entity.account.Account, name='Account', id=1)
        self.campaign = magic_mixer.blend(core.entity.campaign.Campaign, name='Campaign 1', account_id=1)
        self.campaign_settings = self.campaign.get_current_settings()

        self.campaign_settings.iab_category = dash.constants.IABCategory.IAB1_1
        self.enable_ga_tracking = True
        self.campaign_settings.save(None)

        self.goal = core.goals.campaign_goal.CampaignGoal.objects.create_unsafe(
            campaign=self.campaign,
            type=dash.constants.CampaignGoalKPI.TIME_ON_SITE,
            primary=True,
        )
        start_date = datetime.date.today() - datetime.timedelta(1)
        end_date = datetime.date.today() + datetime.timedelta(10)
        self.credit = magic_mixer.blend(
            core.bcm.CreditLineItem,
            account_id=1, status=1, start_date=start_date, end_date=end_date, amount=100000,
        )
        self.budget = core.bcm.BudgetLineItem.objects.create_unsafe(
            campaign=self.campaign,
            credit=self.credit,
            amount=1000,
            start_date=start_date,
            end_date=end_date,
        )

        self.stats_now = {'visits': 10}
        self.stats_prev = {'visits': 5}
        self.projections = {'pacing': Decimal('90.9')}

        self.ad_group = magic_mixer.blend(core.entity.adgroup.AdGroup, name='Ad Group 1', campaign=self.campaign)
        self.ad_group_settings = self.ad_group.get_current_settings()
        self.ad_group_settings.start_date = start_date
        self.ad_group_settings.end_date = end_date
        self.ad_group_settings.state = dash.constants.AdGroupSettingsState.ACTIVE
        self.ad_group_settings.save(None)

    def test_primary_goal(self):
        self.goal.delete()

        self.assertEqual(
            delivery.check_campaign_delivery(self.campaign, self.campaign_settings,
                                             self.stats_now, self.stats_prev, self.projections),
            constants.CampaignDeliveryStatus.NO_GOAL
        )

        goal = core.goals.campaign_goal.CampaignGoal.objects.create_unsafe(
            campaign=self.campaign,
            type=dash.constants.CampaignGoalKPI.TIME_ON_SITE,
            primary=False,
        )

        self.assertEqual(
            delivery.check_campaign_delivery(self.campaign, self.campaign_settings,
                                             self.stats_now, self.stats_prev, self.projections),
            constants.CampaignDeliveryStatus.NO_GOAL
        )

        goal.primary = True
        goal.save()

        self.assertEqual(
            delivery.check_campaign_delivery(self.campaign, self.campaign_settings,
                                             self.stats_now, self.stats_prev, self.projections),
            constants.CampaignDeliveryStatus.OK
        )

    def test_iab(self):
        self.campaign_settings.iab_category = dash.constants.IABCategory.IAB24
        self.assertEqual(
            delivery.check_campaign_delivery(self.campaign, self.campaign_settings,
                                             self.stats_now, self.stats_prev, self.projections),
            constants.CampaignDeliveryStatus.IAB_UNDEFINED
        )

    def test_budget(self):
        campaign = magic_mixer.blend(core.entity.campaign.Campaign, name='Campaign 2', account_id=1)
        campaign_settings = campaign.get_current_settings()
        campaign_settings.iab_category = dash.constants.IABCategory.IAB1_1
        campaign_settings.save(None)

        core.goals.campaign_goal.CampaignGoal.objects.create_unsafe(
            campaign=campaign,
            type=dash.constants.CampaignGoalKPI.TIME_ON_SITE,
            primary=True,
        )
        self.assertEqual(
            delivery.check_campaign_delivery(campaign, campaign_settings, self.stats_now,
                                             self.stats_prev, self.projections),
            constants.CampaignDeliveryStatus.NO_BUDGET
        )

    def test_missing_postclick_stats(self):
        self.assertEqual(
            delivery.check_campaign_delivery(self.campaign, self.campaign_settings, {}, {}, self.projections),
            constants.CampaignDeliveryStatus.MISSING_POSTCLICK_STATS
        )
        self.assertEqual(
            delivery.check_campaign_delivery(self.campaign, self.campaign_settings, {
                                             'visits': 0}, {'visits': 0}, self.projections),
            constants.CampaignDeliveryStatus.MISSING_POSTCLICK_STATS
        )
        self.assertEqual(
            delivery.check_campaign_delivery(self.campaign, self.campaign_settings,
                                             {'visits': 10}, {}, self.projections),
            constants.CampaignDeliveryStatus.OK
        )
        self.assertEqual(
            delivery.check_campaign_delivery(self.campaign, self.campaign_settings, {
                                             'visits': 0}, {'visits': 5}, self.projections),
            constants.CampaignDeliveryStatus.OK
        )

    def test_missing_postclick_setup(self):
        campaign_settings = self.campaign.get_current_settings().copy_settings()
        campaign_settings.enable_ga_tracking = False
        campaign_settings.enable_adobe_tracking = False
        campaign_settings.save(None)
        self.assertEqual(
            delivery.check_campaign_delivery(self.campaign, campaign_settings,
                                             self.stats_now, self.stats_prev, self.projections),
            constants.CampaignDeliveryStatus.MISSING_POSTCLICK_SETUP
        )

        campaign_settings = self.campaign.get_current_settings().copy_settings()
        campaign_settings.enable_ga_tracking = False
        campaign_settings.enable_adobe_tracking = True
        campaign_settings.save(None)
        self.assertEqual(
            delivery.check_campaign_delivery(self.campaign, campaign_settings,
                                             self.stats_now, self.stats_prev, self.projections),
            constants.CampaignDeliveryStatus.OK
        )

    def test_pacing(self):
        self.assertEqual(
            delivery.check_campaign_delivery(self.campaign, self.campaign_settings, self.stats_now, self.stats_prev, {
                'pacing': Decimal('10.10')
            }),
            constants.CampaignDeliveryStatus.LOW_PACING
        )
        self.assertEqual(
            delivery.check_campaign_delivery(self.campaign, self.campaign_settings, self.stats_now, self.stats_prev, {
                'pacing': Decimal('220.99')
            }),
            constants.CampaignDeliveryStatus.HIGH_PACING
        )
        self.assertEqual(
            delivery.check_campaign_delivery(self.campaign, self.campaign_settings, self.stats_now, self.stats_prev, {
                'pacing': Decimal('220.99')
            }, check_pacing=False),
            constants.CampaignDeliveryStatus.OK
        )

    def test_active_ad_groups(self):
        s = self.ad_group_settings.copy_settings()
        s.state = dash.constants.AdGroupSettingsState.INACTIVE
        s.save(None)

        self.assertEqual(
            delivery.check_campaign_delivery(self.campaign, self.campaign_settings,
                                             self.stats_now, self.stats_prev, self.projections),
            constants.CampaignDeliveryStatus.NO_ACTIVE_AD_GROUPS
        )

        s = self.ad_group_settings.copy_settings()
        s.state = dash.constants.AdGroupSettingsState.ACTIVE
        s.end_date = s.start_date
        s.save(None)

        self.assertEqual(
            delivery.check_campaign_delivery(self.campaign, self.campaign_settings,
                                             self.stats_now, self.stats_prev, self.projections),
            constants.CampaignDeliveryStatus.NO_ACTIVE_AD_GROUPS
        )

        s = self.ad_group_settings.copy_settings()
        s.state = dash.constants.AdGroupSettingsState.ACTIVE
        s.end_date = None
        s.save(None)

        self.assertEqual(
            delivery.check_campaign_delivery(self.campaign, self.campaign_settings,
                                             self.stats_now, self.stats_prev, self.projections),
            constants.CampaignDeliveryStatus.OK
        )


class AdGroupDeliveryTestCase(test.TestCase):

    def setUp(self):
        self.account = magic_mixer.blend(core.entity.account.Account, name='Account', id=1)

        self.campaign = magic_mixer.blend(core.entity.campaign.Campaign, name='Campaign 1', account=self.account)
        self.campaign_settings = self.campaign.get_current_settings()
        self.campaign_settings.save(None)

        self.ad_group = magic_mixer.blend(core.entity.adgroup.AdGroup, name='Ad Group 1', campaign=self.campaign)
        self.ad_group_settings = self.ad_group.get_current_settings()
        self.ad_group_settings.b1_sources_group_enabled = False
        self.ad_group_settings.save(None)

        self.stats = {}

        self.ad = magic_mixer.blend(
            core.entity.contentad.ContentAd,
            title='Zemanta',
            url='http://www.zemanta.com',
            ad_group=self.ad_group
        )
        self.source = magic_mixer.blend(core.source.Source, name='Test Source')

        self.ad_group_source = core.entity.adgroup.AdGroupSource.objects.create_unsafe(
            ad_group=self.ad_group,
            source=self.source
        )
        self.ad_group_source.set_initial_settings(
            None,
            self.ad_group_settings,
            state=1
        )
        self.ad_source = core.entity.contentad.ContentAdSource.objects.create(
            source=self.source,
            content_ad=self.ad,
        )
        self.ad_source.submission_status = dash.constants.ContentAdSubmissionStatus.APPROVED
        self.ad_source.save()

    def test_missing_ads(self):
        self.ad_source.delete()
        self.ad.delete()
        self.assertEqual(
            delivery.check_ad_group_delivery(self.ad_group, self.ad_group_settings, self.stats),
            constants.AdGroupDeliveryStatus.MISSING_ADS
        )

    def test_approved_ads(self):
        self.ad_source.submission_status = dash.constants.ContentAdSubmissionStatus.PENDING
        self.ad_source.save()
        self.assertEqual(
            delivery.check_ad_group_delivery(self.ad_group, self.ad_group_settings, self.stats),
            constants.AdGroupDeliveryStatus.NO_ADS_APPROVED
        )

        self.ad_source.submission_status = dash.constants.ContentAdSubmissionStatus.REJECTED
        self.ad_source.save()
        self.assertEqual(
            delivery.check_ad_group_delivery(self.ad_group, self.ad_group_settings, self.stats),
            constants.AdGroupDeliveryStatus.NO_ADS_APPROVED
        )

        self.ad_source.submission_status = dash.constants.ContentAdSubmissionStatus.APPROVED
        self.ad_source.save()
        self.assertEqual(
            delivery.check_ad_group_delivery(self.ad_group, self.ad_group_settings, self.stats),
            constants.AdGroupDeliveryStatus.OK
        )

    def test_active_sources(self):
        s = self.ad_group_source.get_current_settings().copy_settings()
        s.state = dash.constants.AdGroupSourceSettingsState.INACTIVE
        s.save(None)
        self.assertEqual(
            delivery.check_ad_group_delivery(self.ad_group, self.ad_group_settings, self.stats),
            constants.AdGroupDeliveryStatus.NO_ACTIVE_SOURCES
        )

    def test_active_b1_sources(self):
        s = self.ad_group_settings.copy_settings()
        s.b1_sources_group_enabled = True
        s.b1_sources_group_state = dash.constants.AdGroupSourceSettingsState.ACTIVE
        s.save(None)
        self.assertEqual(
            delivery.check_ad_group_delivery(self.ad_group, s, self.stats),
            constants.AdGroupDeliveryStatus.RTB_AS_1_NO_SOURCES
        )

        source_type = magic_mixer.blend(core.source.SourceType, type='b1')
        source = magic_mixer.blend(core.source.Source, name='Test B1 Source', source_type=source_type)

        ad_group_source = core.entity.adgroup.AdGroupSource.objects.create_unsafe(
            ad_group=self.ad_group,
            source=source
        )
        ad_group_source.set_initial_settings(
            None,
            s,
            state=1
        )
        self.assertEqual(
            delivery.check_ad_group_delivery(self.ad_group, s, self.stats),
            constants.AdGroupDeliveryStatus.OK
        )

    def test_interest_b1_sources(self):
        source_type = magic_mixer.blend(core.source.SourceType, type='b1')
        self.source.source_type = source_type
        self.source.save()

        s = self.ad_group_settings.copy_settings()
        s.interest_targeting = ['finance']
        s.save(None)

        self.assertEqual(
            delivery.check_ad_group_delivery(self.ad_group, s, self.stats),
            constants.AdGroupDeliveryStatus.TOO_LITTLE_B1_SOURCES_FOR_INTEREST_TARGETING
        )

        for i in range(6):
            source = magic_mixer.blend(core.source.Source, name='Test B1 Source {}'.format(i), source_type=source_type)
            ad_group_source = core.entity.adgroup.AdGroupSource.objects.create_unsafe(
                ad_group=self.ad_group,
                source=source
            )
            ad_group_source.set_initial_settings(
                None,
                s,
                state=1
            )
        self.assertEqual(
            delivery.check_ad_group_delivery(self.ad_group, s, self.stats),
            constants.AdGroupDeliveryStatus.OK
        )

    def test_whitelist_publisher_groups(self):
        s = self.ad_group_settings.copy_settings()
        s.whitelist_publisher_groups = [1]
        s.save(None)
        self.assertEqual(
            delivery.check_ad_group_delivery(self.ad_group, s, self.stats),
            constants.AdGroupDeliveryStatus.OK
        )

        s = s.copy_settings()
        s.interest_targeting = ['finance']
        s.bluekai_targeting = []
        s.save(None)
        self.assertEqual(
            delivery.check_ad_group_delivery(self.ad_group, s, self.stats),
            constants.AdGroupDeliveryStatus.WHITELIST_AND_INTERESTS
        )

        s = s.copy_settings()
        s.interest_targeting = []
        s.bluekai_targeting = ['OR', 'bluekai:123']
        s.save(None)
        self.assertEqual(
            delivery.check_ad_group_delivery(self.ad_group, s, self.stats),
            constants.AdGroupDeliveryStatus.WHITELIST_AND_DATA
        )

    def test_missing_data_cost(self):
        s = self.ad_group_settings.copy_settings()
        s.bluekai_targeting = ['OR', 'bluekai:123']
        s.save(None)

        self.assertEqual(
            delivery.check_ad_group_delivery(self.ad_group, s, {'media': 100, 'data': 0}),
            constants.AdGroupDeliveryStatus.MISSING_DATA_COST
        )

        s = self.ad_group_settings.copy_settings()
        s.bluekai_targeting = [u'not', u'outbrain:custom_eng_1', 'bluekai:1234']
        s.save(None)

        self.assertEqual(
            delivery.check_ad_group_delivery(self.ad_group, s, {'media': 100, 'data': 0}),
            constants.AdGroupDeliveryStatus.MISSING_DATA_COST
        )

        s = self.ad_group_settings.copy_settings()
        s.bluekai_targeting = ['OR', ['AND', 'bluekai:123', 'bluekai:345'], ['AND', 'bluekai:567', 'bluekai:789']]
        s.save(None)

        self.assertEqual(
            delivery.check_ad_group_delivery(self.ad_group, s, {'media': 100, 'data': 0}),
            constants.AdGroupDeliveryStatus.MISSING_DATA_COST
        )

    def test_missing_data_cost_unbillable(self):
        s = self.ad_group_settings.copy_settings()
        s.bluekai_targeting = ['OR', 'outbrain:123', 'lr-DataStore:123', ['lotame:123']]
        s.save(None)

        self.assertEqual(
            delivery.check_ad_group_delivery(self.ad_group, s, {'media': 100, 'data': 0}),
            constants.AdGroupDeliveryStatus.OK
        )

        s = self.ad_group_settings.copy_settings()
        s.bluekai_targeting = [
            u'not',
            [u'or', u'lr-PayPal:1582823078', u'lr-PayPal:1740944458', u'lr-PayPal:325263093',
             u'lr-PayPal:564635189', u'lr-PayPal:573908747', u'lr-PayPal:727146366', u'lr-PayPal:1892779779', u'lr-PayPal:1022665586']
        ]
        s.save(None)
        self.assertEqual(
            delivery.check_ad_group_delivery(self.ad_group, s, {'media': 100, 'data': 0}),
            constants.AdGroupDeliveryStatus.OK
        )

    def test_missing_video_cost(self):
        asset = dash.features.videoassets.models.VideoAsset(name='test', account=self.account)
        asset.save()

        self.ad.video_asset = asset
        self.ad.save()

        stats = {}
        stats.update(self.stats)
        stats['media'] = 100

        self.assertEqual(
            delivery.check_ad_group_delivery(self.ad_group, self.ad_group_settings, stats),
            constants.AdGroupDeliveryStatus.MISSING_VIDEO_COST
        )

        stats['data'] = 100
        self.assertEqual(
            delivery.check_ad_group_delivery(self.ad_group, self.ad_group_settings, stats),
            constants.AdGroupDeliveryStatus.OK
        )
