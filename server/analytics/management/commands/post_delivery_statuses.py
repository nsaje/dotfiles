from decimal import Decimal

import influx

import analytics.delivery
import utils.command_helpers


def cap_to_category(cap):
    if not cap or cap <= Decimal('10'):
        return '0-10'
    if cap <= Decimal('100'):
        return '10-100'
    if cap <= Decimal('500'):
        return '100-500'
    if cap <= Decimal('1000'):
        return '500-1000'
    return '1000-inf'


class Command(utils.command_helpers.ExceptionCommand):
    help = 'Post delivery statuses to influx'

    def handle(*args, **kwargs):
        reports = analytics.delivery.generate_delivery_reports(skip_ok=True, check_pacing=False, generate_csv=False)

        for name, camp_id, url, cs, campaign_stop, landing_mode, spend, cap, issue in reports['campaign']:
            influx.gauge(
                'campaign_delivery',
                int(spend * 100 / cap) if cap else 0,
                campaign=str(camp_id),
                issue=issue,
                cs=cs.get_short_name() if cs else 'None',
                cap=cap_to_category(cap),
                retentionPolicy="1week"
            )
        for name, adgroup_id, url, cs, campaign_stop, landing_mode, spend, cap, issue in reports['ad_group']:
            influx.gauge(
                'adgroup_delivery',
                int(spend * 100 / cap) if cap else 0,
                adgroup=str(adgroup_id),
                issue=issue,
                cs=cs.get_short_name() if cs else 'None',
                cap=cap_to_category(cap),
                retentionPolicy="1week"
            )
