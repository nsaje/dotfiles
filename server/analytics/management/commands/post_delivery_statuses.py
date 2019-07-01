from decimal import Decimal

import influx

import analytics.constants
import analytics.delivery
import utils.command_helpers


def cap_to_category(cap):
    if not cap or cap <= Decimal("10"):
        return "0-10"
    if cap <= Decimal("100"):
        return "10-100"
    if cap <= Decimal("500"):
        return "100-500"
    if cap <= Decimal("1000"):
        return "500-1000"
    return "1000-inf"


class Command(utils.command_helpers.Z1Command):
    help = "Post delivery statuses to influx"

    def handle(*args, **kwargs):
        reports = analytics.delivery.generate_delivery_reports(skip_ok=True, generate_csv=False)

        for account, camp_id, url, cs, spend, cap, issue, monitoring_paused in reports["campaign"]:
            influx.gauge(
                "campaign_delivery",
                int(spend * 100 / cap) if cap else 0,
                account=account.encode("ascii", errors="ignore").decode(),
                campaign=str(camp_id),
                issue=issue,
                cs=cs.get_full_name().encode("ascii", errors="ignore").decode() if cs else "None",
                cap=cap_to_category(cap),
                retentionPolicy="1week",
                monitoringPaused=monitoring_paused,
            )

        for account, adgroup_id, url, cs, end_date, spend, cap, issue, monitoring_paused in reports["ad_group"]:
            influx.gauge(
                "adgroup_delivery",
                int(spend * 100 / cap) if cap else 0,
                account=account.encode("ascii", errors="ignore").decode(),
                adgroup=str(adgroup_id),
                issue=issue,
                cs=cs.get_full_name().encode("ascii", errors="ignore").decode() if cs else "None",
                cap=cap_to_category(cap),
                retentionPolicy="1week",
                monitoringPaused=monitoring_paused,
            )
