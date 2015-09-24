import logging
import dateutil
from optparse import make_option
from django.db.models import Max, Min

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

        min_id = max(models.ArticleStats.objects.aggregate(Min('id')), start_id)
        max_id = models.ArticleStats.objects.aggregate(Max('id'))

        try:
            with open(options.get('filename', 'a+')) as f:
                for batch_start_id in range(min_id, BATCH_SIZE, max_id):
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

"""
    dump struktura
    id integer IDENTITY PRIMARY KEY,
    date date,
    content_ad_id integer,
    adgroup_id integer,
    source_id integer,
    campaign_id integer,
    account_id integer,

    impressions integer,
    clicks integer,
    cost_cc integer,
    data_cost_cc integer,

    visits integer,
    new_visits integer,
    bounced_visits integer,
    pageviews integer,
    total_time_on_site integer,

    conversions varchar(512)
)
"""

"""
# traffic metrics
impressions = models.IntegerField(default=0, blank=False, null=False)
clicks = models.IntegerField(default=0, blank=False, null=False)
cost_cc = models.IntegerField(default=0, blank=False, null=False)
data_cost_cc = models.IntegerField(default=0, blank=False, null=False)

# postclick metrics
visits = models.IntegerField(default=0, blank=False, null=False)
new_visits = models.IntegerField(default=0, blank=False, null=False)
bounced_visits = models.IntegerField(default=0, blank=False, null=False)
pageviews = models.IntegerField(default=0, blank=False, null=False)
duration = models.IntegerField(default=0, blank=False, null=False)

has_traffic_metrics = models.IntegerField(default=0, blank=False, null=False)
has_postclick_metrics = models.IntegerField(default=0, blank=False, null=False)
has_conversion_metrics = models.IntegerField(default=0, blank=False, null=False)

class Meta:
    abstract = True


class ArticleStats(StatsMetrics):

datetime = models.DateTimeField()

ad_group = models.ForeignKey('dash.AdGroup', on_delete=models.PROTECT)
article = models.ForeignKey('dash.Article', on_delete=models.PROTECT)
source = models.ForeignKey('dash.Source', on_delete=models.PROTECT)

created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
"""
