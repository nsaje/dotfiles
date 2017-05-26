import logging
from operator import itemgetter

from dash import infobox_helpers
from utils import k1_helper
from utils import lc_helper

logger = logging.getLogger(__name__)


def get_adgroup_infobox_spend(user, ad_group, filtered_sources):
    if not user.has_perm('zemauth.can_see_realtime_spend'):
        return []

    total_today_spend = 'N/A'
    try:
        stats = k1_helper.get_adgroup_realtimestats(ad_group.id)
        sources_by_slug = {source.bidder_slug: source for source in filtered_sources}
        stats = _filter_sources(stats, sources_by_slug)
        stats = sorted(stats, key=itemgetter('spend'), reverse=True)
        total_today_spend = lc_helper.default_currency(
            sum(stat['spend'] for stat in stats),
            places=4,
        )
    except Exception as e:
        logger.exception(e)
        stats = []

    today_spend = infobox_helpers.OverviewSetting(
        'Today spend:',
        total_today_spend,
        internal=not user.get_all_permissions_with_access_levels().get('zemauth.can_see_realtime_spend'),
        warning='''Today's spend is calculated in real-time and represents the amount of money spent on media and data costs today.
        Today's spend does not include fees that might apply.
The final amount might be different due to post-processing.
Outbrain, Yahoo and Facebook today's spend is not available.''',
    )
    today_spend = today_spend.comment('', '<br />'.join(_format_source_spend(stat) for stat in stats))

    return [today_spend.as_dict()]


def _format_source_spend(source_stat):
    return '{name}: {spend}'.format(
        name=source_stat['source'].name,
        spend=lc_helper.default_currency(source_stat['spend'], places=4),
    )


def _filter_sources(stats, sources_by_slug):
    for stat in stats:
        if stat['source_slug'] in sources_by_slug:
            yield {
                'source': sources_by_slug[stat['source_slug']],
                'spend': stat['spend'],
            }
