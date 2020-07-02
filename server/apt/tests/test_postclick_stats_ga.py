import core.models
import redshiftapi.db
from dash.constants import GATrackingType
from utils import dates_helper
from utils import metrics_compat

from ..base.test_case import APTTestCase


class PostclickStatsGaAPTTest(APTTestCase):
    def test_ga_api(self):
        query = """
            SELECT c.id from dash_campaign c
            JOIN dash_campaignsettings cs
            ON c.settings_id = cs.id
            JOIN dash_galinkedaccounts ga
            ON ga.customer_ga_account_id = split_part(cs.ga_property_id, '-', {ga_type})
            WHERE cs.archived = false AND cs.enable_ga_tracking = true AND cs.ga_tracking_type = 2 AND cs.ga_property_id <> ''
            ORDER BY RANDOM()
        """.format(
            ga_type=GATrackingType.API
        )

        campaign_ids = [str(campaign.id) for campaign in core.models.Campaign.objects.raw(query)]

        account_query = """
            SELECT account_id from mv_campaign
            WHERE campaign_id in ({campaign_ids_str}) AND date = %s
            GROUP BY account_id
            HAVING SUM(cost_nano) > 0 AND SUM(visits) is {visits_is}
        """

        with redshiftapi.db.get_write_stats_cursor() as c:
            c.execute(
                account_query.format(campaign_ids_str=",".join(campaign_ids), visits_is="not null"),
                [dates_helper.local_yesterday()],
            )
            nr_account_with_ga_data = len(redshiftapi.db.dictfetchall(c))

            c.execute(
                account_query.format(campaign_ids_str=",".join(campaign_ids), visits_is="null"),
                [dates_helper.local_yesterday()],
            )
            nr_account_without_ga_data = len(redshiftapi.db.dictfetchall(c))

        metrics_compat.gauge("ga_linked_and_spending_accounts_with_data", nr_account_with_ga_data)
        metrics_compat.gauge("ga_linked_and_spending_accounts_without_data", nr_account_without_ga_data)

        self.assertGreater(nr_account_with_ga_data / (nr_account_with_ga_data + nr_account_without_ga_data), 0.5)
