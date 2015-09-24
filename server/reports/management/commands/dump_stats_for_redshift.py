import logging
import dateutil
from optparse import make_option

from reports import models

from django.core.management import BaseCommand

logger = logging.getLogger(__name__)

DELIMITER = '|'
BATCH_SIZE = 100000


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--start_id', dest='start_id', default=0, help='Dump ArticleStats starting with id.'),
        make_option('--end_date', dest='end_date', default=None, help='Dump ArticleStats up to date.'),
        make_option('--file', dest='filename', default='./articlestats', help='File to which data will be written'),
    )

    def handle(self, *args, **options):
        start_id = int(options.get('start_id', 0))
        end_date = None
        if options.get('end_date') is not None:
            end_date = dateutil.parser.parse(options['end_date']).date()

        min_id = max(models.ArticleStats.objects.all().order_by('id').first() or 0, start_id)
        max_id = models.ArticleStats.objects.all().order_by('-id').first() or 0

        try:
            with open(options.get('filename'), 'w') as f:
                for batch_start_id in range(min_id, max_id, BATCH_SIZE):
                    current_batch = models.ArticleStats.objects.filter(
                        id__gte=batch_start_id,
                        id__lte=batch_start_id+BATCH_SIZE
                    )
                    if end_date is not None:
                        current_batch = current_batch.filter(date__lte=end_date)

                    for article_stats in current_batch:
                        # article_stats.id - can't dump id's
                        data = [
                            article_stats.date.isoformat(),
                            article_stats.content_ad.id,
                            0, # special id instead of content ad
                            article_stats.ad_group.id,
                            article_stats.source.id,
                            article_stats.ad_group.campaign.id,
                            article_stats.ad_group.campaign.account.id,

                            article_stats.impressions,
                            article_stats.clicks,
                            article_stats.cost_cc,
                            article_stats.data_cost_cc,

                            article_stats.visits,
                            article_stats.new_visits,
                            article_stats.bounced_visits,
                            article_stats.pageviews,
                            article_stats.duration,
                            ''  # TODO: Conversions?
                        ]
                        f.write(DELIMITER.join(map(str, data)) + '\n')

        except:
            logger.exception('Failed outputting articlestats')
