import logging
from django.core.management.base import BaseCommand
import reports
from automation import helpers, autopilot
from freezegun import freeze_time
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    @freeze_time("2015-04-20 18:05:05", tz_offset=-4)
    def handle(self, *args, **options):
        logger.info('Running bid CPC adjusting Auto-Pilot.')

        for camp in helpers.get_active_campaigns():
            adgroupChanges = {}
            for adg in helpers.get_active_ad_groups(camp):

                    yesterday_spends = reports.api.get_yesterday_cost(ad_group=adg)
                    for ad_group_source_settings in autopilot.get_autopilot_ad_group_sources_settings(adg):
                        if autopilot.ad_group_sources_daily_budget_was_changed_recently(ad_group_source_settings.ad_group_source):
                            continue

                        yesterday_spend = yesterday_spends.get(ad_group_source_settings.ad_group_source.source_id)

                        proposed_cpc = autopilot.calculate_new_autopilot_cpc(
                            ad_group_source_settings.cpc_cc,
                            ad_group_source_settings.daily_budget_cc,
                            yesterday_spend
                        )

                        if ad_group_source_settings.cpc_cc == proposed_cpc:
                            continue

                        autopilot.persist_cpc_change_to_admin_log(
                            ad_group_source_settings.ad_group_source,
                            yesterday_spend,
                            ad_group_source_settings.cpc_cc,
                            proposed_cpc,
                            ad_group_source_settings.daily_budget_cc
                        )

                        autopilot.update_ad_group_source_cpc(
                            ad_group_source_settings.ad_group_source,
                            proposed_cpc
                        )

                        if adg.name not in adgroupChanges:
                            adgroupChanges[adg.name] = []
                        adgroupChanges[adg.name].append([
                            ad_group_source_settings.ad_group_source.source.name,
                            ad_group_source_settings.cpc_cc,
                            proposed_cpc
                        ])

            if adgroupChanges != {}:
                autopilot.send_autopilot_CPC_changes_email(
                    camp.name,
                    camp.id,
                    camp.account.name,
                    [camp.get_current_settings().account_manager.email],
                    adgroupChanges
                )
