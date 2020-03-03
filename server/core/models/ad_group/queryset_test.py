from django.test import TestCase

import core
import utils.dates_helper
from dash import constants
from utils.magic_mixer import magic_mixer

from . import model


class AdGroupQuerysetTest(TestCase):
    def test_filter_active(self):
        campaign = magic_mixer.blend(core.models.Campaign, settings_archived=True)
        adgroup = magic_mixer.blend(core.models.AdGroup, campaign=campaign, archived=True)
        ad_group_source = magic_mixer.blend(core.models.AdGroupSource, ad_group=adgroup)

        ad_group_source.settings.update_unsafe(None, state=constants.AdGroupSourceSettingsState.INACTIVE)

        groups = model.AdGroup.objects.all().filter_at_least_one_source_running()
        self.assertEqual(len(groups), 0)

        campaign.settings.update_unsafe(None, archived=False)
        adgroup.settings.update_unsafe(None, archived=False)
        ad_group_source.settings.update_unsafe(None, state=constants.AdGroupSourceSettingsState.ACTIVE)

        groups = model.AdGroup.objects.all().filter_at_least_one_source_running()
        self.assertEqual(len(groups), 1)

    def test_filter_current_and_active(self):
        campaign = magic_mixer.blend(core.models.Campaign)
        adgroup = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        adgroup.settings.update_unsafe(
            None,
            state=constants.AdGroupSettingsState.INACTIVE,
            start_date=utils.dates_helper.days_after(utils.dates_helper.local_today(), 5),
            end_date=utils.dates_helper.local_today(),
        )

        groups = model.AdGroup.objects.all().filter_current_and_active()
        self.assertEqual(len(groups), 0)

        adgroup.settings.update_unsafe(
            None,
            state=constants.AdGroupSettingsState.ACTIVE,
            start_date=utils.dates_helper.local_yesterday(),
            end_date=utils.dates_helper.days_after(utils.dates_helper.local_today(), 5),
        )

        groups = model.AdGroup.objects.all().filter_current_and_active()
        self.assertEqual(len(groups), 1)

    def test_filter_allowed_to_run(self):
        campaign = magic_mixer.blend(core.models.Campaign, real_time_campaign_stop=False)
        magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        groups = model.AdGroup.objects.all().filter_allowed_to_run()
        self.assertEqual(len(groups), 1)

        campaign.real_time_campaign_stop = True
        campaign.save()

        groups = model.AdGroup.objects.all().filter_allowed_to_run()
        self.assertEqual(len(groups), 0)

    def test_all_filters(self):
        campaign = magic_mixer.blend(core.models.Campaign, archived=False)
        adgroup = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        ad_group_source = magic_mixer.blend(core.models.AdGroupSource, ad_group=adgroup)

        adgroup.settings.update_unsafe(
            None,
            archived=False,
            state=constants.AdGroupSettingsState.ACTIVE,
            start_date=utils.dates_helper.local_yesterday(),
            end_date=utils.dates_helper.days_after(utils.dates_helper.local_today(), 5),
        )
        ad_group_source.settings.update_unsafe(None, state=constants.AdGroupSourceSettingsState.ACTIVE)

        groups = model.AdGroup.objects.all().filter_running_and_has_budget()
        self.assertEqual(len(groups), 1)
