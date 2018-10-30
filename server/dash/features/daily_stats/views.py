import dash.views.helpers
import stats.api_breakdowns
import stats.api_dailystats
import stats.constraints_helper
from dash import campaign_goals
from dash import constants
from dash import models
from utils import api_common
from utils import columns
from utils import db_for_reads
from utils import exc

from . import helpers

MAX_DAILY_STATS_BREAKDOWNS = 3


class BaseDailyStatsView(api_common.BaseApiView):
    def extract_params(self, request, selected_only):
        view_filter = dash.views.helpers.ViewFilter(request)
        return {
            "user": request.user,
            "start_date": view_filter.start_date,
            "end_date": view_filter.end_date,
            "filtered_sources": view_filter.filtered_sources,
            "show_archived": view_filter.show_archived,
            "only_used_sources": False,
        }

    def get_stats(self, request, group_key, should_use_publishers_view=False):
        # FIXME (jurebajt): Totals are always requested because 'false' is truthy
        totals = request.GET.get("totals")
        metrics = request.GET.getlist("metrics")

        constraints = self.prepare_constraints(request)
        currency = self._get_currency_from_constraints(request.user, constraints)

        result = []
        if totals:
            result += self.get_stats_totals(
                request, metrics, currency, should_use_publishers_view=should_use_publishers_view
            )

        if self.selected_objects:
            result += self.get_stats_selected(
                request,
                metrics,
                currency,
                group_key,
                [obj.id for obj in self.selected_objects],
                should_use_publishers_view=should_use_publishers_view,
            )

        return {"chart_data": result, "currency": currency}

    def validate_metrics(self, metrics, pixels=[], conversion_goals=[], uses_bcm_v2=True):
        column_mapping = columns.custom_field_to_column_name_mapping(pixels, conversion_goals, uses_bcm_v2=uses_bcm_v2)
        for metric in metrics:
            if not columns.get_column_name(metric, mapping=column_mapping, raise_exception=False):
                raise exc.ValidationError("Invalid metric")

    def get_stats_totals(self, request, metrics, currency, should_use_publishers_view):
        breakdown = ["day"]

        constraints = self.prepare_constraints(request)
        goals = stats.api_breakdowns.get_goals(constraints, breakdown)

        query_results = stats.api_dailystats.query(
            request.user,
            self.level,
            breakdown,
            metrics,
            constraints,
            goals,
            "day",
            should_use_publishers_view=should_use_publishers_view,
        )

        stats.helpers.update_rows_to_contain_values_in_currency(query_results, currency)

        return helpers.format_metrics(query_results, metrics, {"totals": "Totals"}, default_group="totals")

    def get_stats_selected(self, request, metrics, currency, group_key, selected_ids, should_use_publishers_view):
        join_selected = len(selected_ids) > MAX_DAILY_STATS_BREAKDOWNS

        breakdown = ["day"]
        if not join_selected:
            breakdown.append(group_key)

        constraints = self.prepare_constraints(request, selected_only=True)
        goals = stats.api_breakdowns.get_goals(constraints, breakdown)
        query_results = stats.api_dailystats.query(
            request.user,
            self.level,
            breakdown,
            metrics,
            constraints,
            goals,
            "day",
            should_use_publishers_view=should_use_publishers_view,
        )

        stats.helpers.update_rows_to_contain_values_in_currency(query_results, currency)

        if join_selected:
            return helpers.format_metrics(query_results, metrics, {"selected": "Selected"}, default_group="selected")
        else:
            return helpers.format_metrics(
                query_results, metrics, helpers.get_object_mapping(self.selected_objects), group_key=group_key
            )

    def _get_selected_objects(self, request, objects):
        select_all = request.GET.get("select_all", False)
        select_batch_id = request.GET.get("select_batch")
        selected_ids = [int(id) for id in request.GET.getlist("selected_ids")]
        not_selected_ids = [int(id) for id in request.GET.getlist("not_selected_ids")]
        return dash.views.helpers.get_selected_entities(
            objects, select_all, selected_ids, not_selected_ids, True, select_batch_id
        )

    def get_goals(self, request, conversion_goals=None, campaign=None, pixels=None):
        user = request.user
        view_filter = dash.views.helpers.ViewFilter(request)
        start_date = view_filter.start_date
        end_date = view_filter.end_date

        result = {}
        if conversion_goals is not None:
            result["conversion_goals"] = dash.views.helpers.get_conversion_goals_wo_pixels(conversion_goals)

        if pixels:
            result["pixels"] = dash.views.helpers.get_pixels_list(pixels)

        can_see_campaign_goals = user.has_perm("zemauth.campaign_goal_performance")
        if campaign is not None and can_see_campaign_goals:
            result["goal_fields"] = campaign_goals.inverted_campaign_goal_map(
                conversion_goals, uses_bcm_v2=campaign.account.uses_bcm_v2
            )

            result["campaign_goals"] = dict(
                campaign_goals.get_campaign_goal_metrics(campaign, start_date, end_date, local_values=True)
            )
            if conversion_goals:
                result["campaign_goals"].update(
                    campaign_goals.get_campaign_conversion_goal_metrics(
                        campaign, start_date, end_date, conversion_goals
                    )
                )
        return result

    def _get_currency_from_constraints(self, user, constraints):
        if constraints.get("allowed_accounts"):
            return stats.helpers.get_report_currency(user, constraints["allowed_accounts"])
        elif constraints.get("account"):
            return stats.helpers.get_report_currency(user, [constraints["account"]])


class AllAccountsDailyStatsView(BaseDailyStatsView):
    level = constants.Level.ALL_ACCOUNTS

    def prepare_constraints(self, request, selected_only=False):
        params = self.extract_params(request, selected_only)
        return stats.constraints_helper.prepare_all_accounts_constraints(**params)

    def extract_params(self, request, selected_only):
        params = super(AllAccountsDailyStatsView, self).extract_params(request, selected_only)
        params["filtered_agencies"] = self.view_filter.filtered_agencies
        params["filtered_account_types"] = self.view_filter.filtered_account_types
        return params


class AllAccountsAccountsDailyStats(AllAccountsDailyStatsView):
    def extract_params(self, request, selected_only):
        params = super(AllAccountsAccountsDailyStats, self).extract_params(request, selected_only)
        if selected_only:
            params["filtered_accounts"] = self.selected_objects
        return params

    @db_for_reads.use_stats_read_replica()
    def get(self, request):
        if not request.user.has_perm("zemauth.all_accounts_accounts_view"):
            raise exc.MissingDataError()

        self.view_filter = dash.views.helpers.ViewFilter(request=request)
        accounts = (
            models.Account.objects.all()
            .filter_by_user(request.user)
            .filter_by_agencies(self.view_filter.filtered_agencies)
            .filter_by_account_types(self.view_filter.filtered_account_types)
        )
        uses_bcm_v2 = dash.views.helpers.all_accounts_uses_bcm_v2(request.user)

        self.validate_metrics(request.GET.getlist("metrics"), uses_bcm_v2=uses_bcm_v2)

        self.selected_objects = self._get_selected_objects(request, accounts)

        return self.create_api_response(self.get_stats(request, "account_id"))


class AllAccountsSourcesDailyStats(AllAccountsDailyStatsView):
    def extract_params(self, request, selected_only):
        params = super(AllAccountsSourcesDailyStats, self).extract_params(request, selected_only)
        if selected_only:
            params["filtered_sources"] = params["filtered_sources"].filter(
                id__in=self.selected_objects.values_list("pk", flat=True)
            )
        return params

    @db_for_reads.use_stats_read_replica()
    def get(self, request):
        if not request.user.has_perm("zemauth.all_accounts_accounts_view"):
            raise exc.MissingDataError()

        self.view_filter = dash.views.helpers.ViewFilter(request=request)
        uses_bcm_v2 = dash.views.helpers.all_accounts_uses_bcm_v2(request.user)

        self.validate_metrics(request.GET.getlist("metrics"), uses_bcm_v2=uses_bcm_v2)

        sources = models.Source.objects.all()

        self.selected_objects = self._get_selected_objects(request, sources)

        return self.create_api_response(self.get_stats(request, "source_id"))


class AllAccountsPublishersDailyStats(AllAccountsDailyStatsView):
    def extract_params(self, request, selected_only):
        params = super(AllAccountsPublishersDailyStats, self).extract_params(request, selected_only)
        params["show_blacklisted_publishers"] = request.GET.get(
            "show_blacklisted_publishers", constants.PublisherBlacklistFilter.SHOW_ALL
        )
        return params

    @db_for_reads.use_stats_read_replica()
    def get(self, request):
        if not request.user.has_perm("zemauth.can_see_publishers"):
            raise exc.MissingDataError()

        self.view_filter = dash.views.helpers.ViewFilter(request=request)
        uses_bcm_v2 = dash.views.helpers.all_accounts_uses_bcm_v2(request.user)

        self.validate_metrics(request.GET.getlist("metrics"), uses_bcm_v2=uses_bcm_v2)

        self.selected_objects = None

        return self.create_api_response(self.get_stats(request, None, should_use_publishers_view=True))


class AccountDailyStatsView(BaseDailyStatsView):
    level = constants.Level.ACCOUNTS

    def prepare_constraints(self, request, selected_only=False):
        params = self.extract_params(request, selected_only)
        return stats.constraints_helper.prepare_account_constraints(**params)

    def extract_params(self, request, selected_only):
        params = super(AccountDailyStatsView, self).extract_params(request, selected_only)
        params["account"] = self.account
        return params


class AccountCampaignsDailyStats(AccountDailyStatsView):
    def extract_params(self, request, selected_only):
        params = super(AccountCampaignsDailyStats, self).extract_params(request, selected_only)
        if selected_only:
            params["filtered_campaigns"] = self.selected_objects
        return params

    @db_for_reads.use_stats_read_replica()
    def get(self, request, account_id):
        self.account = dash.views.helpers.get_account(request.user, account_id)
        pixels = self.account.conversionpixel_set.filter(archived=False)
        self.validate_metrics(request.GET.getlist("metrics"), pixels=pixels, uses_bcm_v2=self.account.uses_bcm_v2)

        campaigns = self.account.campaign_set.all().filter_by_user(request.user)
        self.selected_objects = self._get_selected_objects(request, campaigns)

        return self.create_api_response(
            helpers.merge(self.get_stats(request, "campaign_id"), self.get_goals(request, pixels=pixels))
        )


class AccountSourcesDailyStats(AccountDailyStatsView):
    def extract_params(self, request, selected_only):
        params = super(AccountSourcesDailyStats, self).extract_params(request, selected_only)
        if selected_only:
            params["filtered_sources"] = params["filtered_sources"].filter(
                id__in=self.selected_objects.values_list("pk", flat=True)
            )
        return params

    @db_for_reads.use_stats_read_replica()
    def get(self, request, account_id):
        self.account = dash.views.helpers.get_account(request.user, account_id)
        pixels = self.account.conversionpixel_set.filter(archived=False)
        self.validate_metrics(request.GET.getlist("metrics"), pixels=pixels, uses_bcm_v2=self.account.uses_bcm_v2)

        sources = models.Source.objects.all()
        self.selected_objects = self._get_selected_objects(request, sources)

        return self.create_api_response(
            helpers.merge(self.get_stats(request, "source_id"), self.get_goals(request, pixels=pixels))
        )


class AccountPublishersDailyStats(AccountDailyStatsView):
    def extract_params(self, request, selected_only):
        params = super(AccountPublishersDailyStats, self).extract_params(request, selected_only)
        params["show_blacklisted_publishers"] = request.GET.get(
            "show_blacklisted_publishers", constants.PublisherBlacklistFilter.SHOW_ALL
        )
        return params

    @db_for_reads.use_stats_read_replica()
    def get(self, request, account_id):
        if not request.user.has_perm("zemauth.can_see_publishers"):
            raise exc.MissingDataError()

        self.account = dash.views.helpers.get_account(request.user, account_id)

        pixels = self.account.conversionpixel_set.filter(archived=False)
        self.validate_metrics(request.GET.getlist("metrics"), pixels=pixels, uses_bcm_v2=self.account.uses_bcm_v2)

        self.selected_objects = None

        return self.create_api_response(
            helpers.merge(
                self.get_stats(request, None, should_use_publishers_view=True), self.get_goals(request, pixels=pixels)
            )
        )


class CampaignDailyStatsView(BaseDailyStatsView):
    level = constants.Level.CAMPAIGNS

    def prepare_constraints(self, request, selected_only=False):
        params = self.extract_params(request, selected_only)
        return stats.constraints_helper.prepare_campaign_constraints(**params)

    def extract_params(self, request, selected_only):
        params = super(CampaignDailyStatsView, self).extract_params(request, selected_only)
        params["campaign"] = self.campaign
        return params


class CampaignAdGroupsDailyStats(CampaignDailyStatsView):
    def extract_params(self, request, selected_only):
        params = super(CampaignAdGroupsDailyStats, self).extract_params(request, selected_only)
        if selected_only:
            params["filtered_ad_groups"] = self.selected_objects
        return params

    @db_for_reads.use_stats_read_replica()
    def get(self, request, campaign_id):
        self.campaign = dash.views.helpers.get_campaign(request.user, campaign_id)
        conversion_goals = self.campaign.conversiongoal_set.all()
        pixels = self.campaign.account.conversionpixel_set.filter(archived=False)
        self.validate_metrics(
            request.GET.getlist("metrics"),
            pixels=pixels,
            conversion_goals=conversion_goals,
            uses_bcm_v2=self.campaign.account.uses_bcm_v2,
        )

        ad_groups = self.campaign.adgroup_set.all()
        self.selected_objects = self._get_selected_objects(request, ad_groups)

        return self.create_api_response(
            helpers.merge(
                self.get_stats(request, "ad_group_id"),
                self.get_goals(request, conversion_goals=conversion_goals, campaign=self.campaign, pixels=pixels),
            )
        )


class CampaignSourcesDailyStats(CampaignDailyStatsView):
    def extract_params(self, request, selected_only):
        params = super(CampaignSourcesDailyStats, self).extract_params(request, selected_only)
        if selected_only:
            params["filtered_sources"] = params["filtered_sources"].filter(
                id__in=self.selected_objects.values_list("pk", flat=True)
            )
        return params

    @db_for_reads.use_stats_read_replica()
    def get(self, request, campaign_id):
        self.campaign = dash.views.helpers.get_campaign(request.user, campaign_id)
        conversion_goals = self.campaign.conversiongoal_set.all()
        pixels = self.campaign.account.conversionpixel_set.filter(archived=False)
        self.validate_metrics(
            request.GET.getlist("metrics"),
            pixels=pixels,
            conversion_goals=conversion_goals,
            uses_bcm_v2=self.campaign.account.uses_bcm_v2,
        )

        sources = models.Source.objects.all()
        self.selected_objects = self._get_selected_objects(request, sources)

        return self.create_api_response(
            helpers.merge(
                self.get_stats(request, "source_id"),
                self.get_goals(request, conversion_goals=conversion_goals, campaign=self.campaign, pixels=pixels),
            )
        )


class CampaignPublishersDailyStats(CampaignDailyStatsView):
    def extract_params(self, request, selected_only):
        params = super(CampaignPublishersDailyStats, self).extract_params(request, selected_only)
        params["show_blacklisted_publishers"] = request.GET.get(
            "show_blacklisted_publishers", constants.PublisherBlacklistFilter.SHOW_ALL
        )
        return params

    @db_for_reads.use_stats_read_replica()
    def get(self, request, campaign_id):
        if not request.user.has_perm("zemauth.can_see_publishers"):
            raise exc.MissingDataError()

        self.campaign = dash.views.helpers.get_campaign(request.user, campaign_id)

        conversion_goals = self.campaign.conversiongoal_set.all()
        pixels = self.campaign.account.conversionpixel_set.filter(archived=False)
        self.validate_metrics(
            request.GET.getlist("metrics"),
            pixels=pixels,
            conversion_goals=conversion_goals,
            uses_bcm_v2=self.campaign.account.uses_bcm_v2,
        )

        self.selected_objects = None

        return self.create_api_response(
            helpers.merge(
                self.get_stats(request, None, should_use_publishers_view=True),
                self.get_goals(request, conversion_goals=conversion_goals, campaign=self.campaign, pixels=pixels),
            )
        )


class AdGroupDailyStatsView(BaseDailyStatsView):
    level = constants.Level.AD_GROUPS

    def prepare_constraints(self, request, selected_only=False):
        params = self.extract_params(request, selected_only)
        return stats.constraints_helper.prepare_ad_group_constraints(**params)

    def extract_params(self, request, selected_only):
        params = super(AdGroupDailyStatsView, self).extract_params(request, selected_only)
        params["ad_group"] = self.ad_group
        return params


class AdGroupContentAdsDailyStats(AdGroupDailyStatsView):
    def extract_params(self, request, selected_only):
        params = super(AdGroupContentAdsDailyStats, self).extract_params(request, selected_only)
        if selected_only:
            params["filtered_content_ads"] = self.selected_objects
        return params

    @db_for_reads.use_stats_read_replica()
    def get(self, request, ad_group_id):
        self.ad_group = dash.views.helpers.get_ad_group(request.user, ad_group_id)
        conversion_goals = self.ad_group.campaign.conversiongoal_set.all()
        pixels = self.ad_group.campaign.account.conversionpixel_set.filter(archived=False)
        self.validate_metrics(
            request.GET.getlist("metrics"),
            pixels=pixels,
            conversion_goals=conversion_goals,
            uses_bcm_v2=self.ad_group.campaign.account.uses_bcm_v2,
        )

        content_ads = self.ad_group.contentad_set.all()
        self.selected_objects = self._get_selected_objects(request, content_ads)

        return self.create_api_response(
            helpers.merge(
                self.get_stats(request, "content_ad_id"),
                self.get_goals(
                    request, conversion_goals=conversion_goals, campaign=self.ad_group.campaign, pixels=pixels
                ),
            )
        )


class AdGroupSourcesDailyStats(AdGroupDailyStatsView):
    def extract_params(self, request, selected_only):
        params = super(AdGroupSourcesDailyStats, self).extract_params(request, selected_only)
        if selected_only:
            params["filtered_sources"] = params["filtered_sources"].filter(
                id__in=self.selected_objects.values_list("pk", flat=True)
            )
        return params

    @db_for_reads.use_stats_read_replica()
    def get(self, request, ad_group_id):
        self.ad_group = dash.views.helpers.get_ad_group(request.user, ad_group_id)
        conversion_goals = self.ad_group.campaign.conversiongoal_set.all()
        pixels = self.ad_group.campaign.account.conversionpixel_set.filter(archived=False)
        self.validate_metrics(
            request.GET.getlist("metrics"),
            pixels=pixels,
            conversion_goals=conversion_goals,
            uses_bcm_v2=self.ad_group.campaign.account.uses_bcm_v2,
        )

        sources = models.Source.objects.all()
        self.selected_objects = self._get_selected_objects(request, sources)

        return self.create_api_response(
            helpers.merge(
                self.get_stats(request, "source_id"),
                self.get_goals(
                    request, conversion_goals=conversion_goals, campaign=self.ad_group.campaign, pixels=pixels
                ),
            )
        )


class AdGroupPublishersDailyStats(AdGroupDailyStatsView):
    def extract_params(self, request, selected_only):
        params = super(AdGroupPublishersDailyStats, self).extract_params(request, selected_only)
        params["show_blacklisted_publishers"] = request.GET.get(
            "show_blacklisted_publishers", constants.PublisherBlacklistFilter.SHOW_ALL
        )
        return params

    @db_for_reads.use_stats_read_replica()
    def get(self, request, ad_group_id):
        if not request.user.has_perm("zemauth.can_see_publishers"):
            raise exc.MissingDataError()

        self.ad_group = dash.views.helpers.get_ad_group(request.user, ad_group_id)

        conversion_goals = self.ad_group.campaign.conversiongoal_set.all()
        pixels = self.ad_group.campaign.account.conversionpixel_set.filter(archived=False)
        self.validate_metrics(
            request.GET.getlist("metrics"),
            pixels=pixels,
            conversion_goals=conversion_goals,
            uses_bcm_v2=self.ad_group.campaign.account.uses_bcm_v2,
        )

        self.selected_objects = None

        return self.create_api_response(
            helpers.merge(
                self.get_stats(request, None, should_use_publishers_view=True),
                self.get_goals(
                    request, conversion_goals=conversion_goals, campaign=self.ad_group.campaign, pixels=pixels
                ),
            )
        )
