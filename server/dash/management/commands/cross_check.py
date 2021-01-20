import collections

from dash import constants
from dash import models
from utils import metrics_compat
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)


class Command(Z1Command):
    def add_arguments(self, parser):
        parser.add_argument("--emit-metrics", action="store_true", default=False, help="Emit metrics")
        parser.add_argument("--verbose", action="store_true", default=False, help="Verbose logging")

    def handle(self, *args, **options):
        running_ad_groups = models.AdGroup.objects.filter_running().select_related("campaign__account", "settings")
        for account, ad_groups in self._group_by_account(running_ad_groups).items():
            num_running_ad_groups, num_running_b1_sources, num_running_ob_sources, num_running_y_sources, num_running_ads = self._get_metrics(
                ad_groups
            )
            self._log_for_account(
                options,
                account,
                len(ad_groups),
                num_running_b1_sources,
                num_running_ob_sources,
                num_running_y_sources,
                num_running_ads,
            )

    def _group_by_account(self, ad_groups):
        ad_groups_by_account = collections.defaultdict(list)
        for ad_group in ad_groups:
            ad_groups_by_account[ad_group.campaign.account].append(ad_group)
        return ad_groups_by_account

    def _get_metrics(self, ad_groups):
        num_running_ads = 0
        num_running_b1_sources = 0
        num_running_ob_sources = 0
        num_running_y_sources = 0
        for ad_group in ad_groups:
            num_running_ads += ad_group.contentad_set.filter(state=constants.ContentAdSourceState.ACTIVE).count()
            ad_group_sources = ad_group.adgroupsource_set.filter(
                settings__state=constants.AdGroupSourceSettingsState.ACTIVE
            )
            num_running_ob_sources += ad_group_sources.filter(
                source__source_type__type=constants.SourceType.OUTBRAIN
            ).count()
            num_running_y_sources += ad_group_sources.filter(
                source__source_type__type=constants.SourceType.YAHOO
            ).count()
            if (
                not ad_group.settings.b1_sources_group_enabled
                or ad_group.settings.b1_sources_group_state == constants.AdGroupSourceSettingsState.ACTIVE
            ):
                num_running_b1_sources += ad_group_sources.filter(
                    source__source_type__type=constants.SourceType.B1
                ).count()
        return len(ad_groups), num_running_b1_sources, num_running_ob_sources, num_running_y_sources, num_running_ads

    def _log_for_account(
        self,
        options,
        account,
        num_running_ad_groups,
        num_running_b1_sources,
        num_running_ob_sources,
        num_running_y_sources,
        num_running_ads,
    ):
        if options.get("verbose"):
            logger.info(
                "Account: %s (id: %s): Running ad groups: %s, b1 sources: %s, ob sources: %s, yahoo sources: %s, ads: %s",
                account.name,
                account.id,
                num_running_ad_groups,
                num_running_b1_sources,
                num_running_ob_sources,
                num_running_y_sources,
                num_running_ads,
            )
        if options.get("emit_metrics"):
            metrics_compat.gauge(
                "consistency_cross_check.running_ad_groups", num_running_ad_groups, account=str(account.id)
            )
            metrics_compat.gauge(
                "consistency_cross_check.running_ad_group_sources",
                num_running_b1_sources,
                account=str(account.id),
                source=str(constants.SourceType.B1),
            )
            metrics_compat.gauge(
                "consistency_cross_check.running_ad_group_sources",
                num_running_ob_sources,
                account=str(account.id),
                source=str(constants.SourceType.OUTBRAIN),
            )
            metrics_compat.gauge(
                "consistency_cross_check.running_ad_group_sources",
                num_running_y_sources,
                account=str(account.id),
                source=str(constants.SourceType.YAHOO),
            )
            metrics_compat.gauge("consistency_cross_check.running_ads", num_running_ads, account=str(account.id))
