import datetime
import logging
import mimetypes

from parse import LandingPageUrl
from models import RawPostclickStats, RawGoalConversionStats
from resolve import resolve_source, resolve_article

import dash.models
import reports.models
import utils.s3helpers

logger = logging.getLogger(__name__)

S3_REPORT_KEY_FORMAT = 'conversionreports/{sender}/{date}/{ts}{ext}'


class ReportEmail(object):

    def __init__(self, sender, recipient, subject, date, text, report):
        self.sender = sender
        self.recipient = recipient
        self.subject = subject
        self.text = text
        self.date = date
        self.report = report

    def _get_goal_name(self, goal_field):
        ix_goal = goal_field.index('(Goal')
        goal_number = ' '.join(goal_field[ix_goal:].split()[:2]) + ')'
        goal_name = goal_field[:ix_goal].strip()
        if len(goal_name) > 16:
            goal_name = goal_name[:13] + '...'
        return goal_name + ' ' + goal_number

    def get_goal_fields(self):
        goal_fields = filter(lambda field: '(Goal' in field, self.report.get_fieldnames())
        result = {}
        for goal_field in goal_fields:
            goal_name = self._get_goal_name(goal_field)
            metric_fields = result.get(goal_name, {})
            if 'Completions)' in goal_field:
                metric_fields['conversions'] = goal_field
            elif 'Value)' in goal_field:
                metric_fields['value'] = goal_field
            result[goal_name] = metric_fields
        return result

    def get_initial_data(self, goal_fields):
        def get_initial_goal_data(goal_fields):
            data = {}
            for goal_name in goal_fields:
                data[goal_name] = {'conversions': 0, 'conversions_value_cc': 0}
            return data

        data = {
            'visits': 0,
            'new_visits': 0,
            'bounced_visits': 0,
            'pageviews': 0,
            'duration': 0,
            'goals': get_initial_goal_data(goal_fields),
        }

        return data

    def add_parsed_metrics(self, data, entry, goal_fields):
        visits = int(entry['Sessions'])
        data['visits'] += visits
        data['new_visits'] += int(entry['New Users'])
        data['bounced_visits'] += int(round(float(entry['Bounce Rate'].replace('%', '')) / 100 * visits))
        data['pageviews'] += int(round(float(entry['Pages / Session']) * visits))
        data['duration'] += visits * self._parse_duration(entry['Avg. Session Duration'])
        for goal_name, metric_fields in goal_fields.items():
            data['goals'][goal_name]['conversions'] += int(entry[metric_fields['conversions']])
            data['goals'][goal_name]['conversions_value_cc'] += int(10000 * float(entry[metric_fields['value']].replace('$', '')))

    def get_stats_by_key(self):

        goal_fields = self.get_goal_fields()

        stats = {}

        for entry in self.report.get_entries():
            url = LandingPageUrl(entry['Landing Page'])
            source = resolve_source(url.source_param)
            if source is None:
                logger.error('ERROR: Cannot resolve source for (ad_group=%s, sender=%s,\
recipient=%s, subject=%s, maildate=%s, \
landing_page_url=%s',
                    url.ad_group_id,
                    self.sender,
                    self.recipient,
                    self.subject,
                    self.date,
                    url.raw_url.decode('ascii', 'ignore')
                 )
                continue

            article = resolve_article(url.clean_url, url.ad_group_id, self.report.get_date(), source)
            if article is None:
                logger.error('ERROR: Cannot resolve article for (ad_group=%s, sender=%s,\
recipient=%s, subject=%s, maildate=%s, \
landing_page_url=%s',
                    url.ad_group_id,
                    self.sender,
                    self.recipient,
                    self.subject,
                    self.date,
                    url.raw_url.decode('ascii', 'ignore')
                 )
                continue

            key = (self.report.get_date(), article.id, url.ad_group_id, source.id)
            
            data = stats.get(key, self.get_initial_data(goal_fields))

            self.add_parsed_metrics(data, entry, goal_fields)

            stats[key] = data

        return stats

    def _parse_duration(self, durstr):
        hours_str, minutes_str, seconds_str = durstr.replace('<', '').split(':')
        return int(seconds_str) + 60*int(minutes_str) + 60*60*int(hours_str)

    def aggregate(self):
        data = self.get_stats_by_key()

        logger.info('Aggregating report email ( \
sender=%s, recipient=%s, \
subject=%s, maildate=%s \
) with total values of (visits=%s, new_visits=%s, \
bounced_visits=%s, pageviews=%s, duration=%s',
            self.sender,
            self.recipient,
            self.subject,
            self.date,
            sum(d['visits'] for d in data.values()),
            sum(d['new_visits'] for d in data.values()),
            sum(d['bounced_visits'] for d in data.values()),
            sum(d['pageviews'] for d in data.values()),
            sum(d['duration'] for d in data.values())
        )

        if data:
            dt, _, ad_group_id, _ = data.keys()[0]
            
            for stats in reports.models.ArticleStats.objects.filter(datetime=dt, ad_group=ad_group_id):
                stats.reset_postclick_metrics()

            for goal_stats in reports.models.GoalConversionStats.objects.filter(datetime=dt, ad_group=ad_group_id):
                goal_stats.reset_metrics()


        for (dt, article_id, ad_group_id, source_id), statvals in data.iteritems():
            article = dash.models.Article.objects.get(id=article_id)
            ad_group = dash.models.AdGroup.objects.get(id=ad_group_id)
            source = dash.models.Source.objects.get(id=source_id)

            try:
                article_stats = reports.models.ArticleStats.objects.get(
                    datetime=dt,
                    article=article,
                    ad_group=ad_group,
                    source=source
                )
            except reports.models.ArticleStats.DoesNotExist:
                article_stats = reports.models.ArticleStats(
                    datetime=dt,
                    article=article,
                    ad_group=ad_group,
                    source=source
                )
            article_stats.visits = statvals['visits']
            article_stats.new_visits = statvals['new_visits']
            article_stats.bounced_visits = statvals['bounced_visits']
            article_stats.pageviews = statvals['pageviews']
            article_stats.duration = statvals['duration']
            article_stats.has_postclick_metrics = 1

            if len(statvals['goals']) > 0:
                article_stats.has_conversion_metrics = 1
            
            for goal_name, goal_stats in statvals['goals'].iteritems():
                try:
                    gcstats = reports.models.GoalConversionStats.objects.get(
                            datetime=dt,
                            article=article,
                            ad_group=ad_group,
                            source=source,
                            goal_name=goal_name
                        )
                except reports.models.GoalConversionStats.DoesNotExist:
                    gcstats = reports.models.GoalConversionStats(
                            datetime=dt,
                            article=article,
                            ad_group=ad_group,
                            source=source,
                            goal_name=goal_name
                        )
                gcstats.conversions = goal_stats['conversions']
                gcstats.conversions_value_cc = goal_stats['conversions_value_cc']
                gcstats.save()

            article_stats.save()

    def save_raw(self):
        goal_fields = self.get_goal_fields()
        dt = self.report.get_date()

        entries = self.report.get_entries()

        ad_group_id = LandingPageUrl(entries[0]['Landing Page']).ad_group_id

        RawPostclickStats.objects.filter(datetime=dt, ad_group_id=ad_group_id).delete()
        RawGoalConversionStats.objects.filter(datetime=dt, ad_group_id=ad_group_id).delete()

        for entry in entries:
            landing_page = LandingPageUrl(entry['Landing Page'])

            assert landing_page.ad_group_id == ad_group_id

            source = resolve_source(landing_page.source_param)
            source_id = source.id if source is not None else None

            metrics_data = self.get_initial_data(goal_fields)
            self.add_parsed_metrics(metrics_data, entry, goal_fields)

            raw_postclick_stats = RawPostclickStats(
                datetime=dt,
                url_raw=landing_page.raw_url,
                url_clean=landing_page.clean_url,
                ad_group_id=int(landing_page.ad_group_id),
                source_id=source_id,
                device_type=entry['Device Category'],
                z1_adgid=str(landing_page.ad_group_id),
                z1_msid=landing_page.source_param,
                z1_did=landing_page.z1_did,
                z1_kid=landing_page.z1_kid,
                z1_tid=landing_page.z1_tid,
                visits=metrics_data['visits'],
                new_visits=metrics_data['new_visits'],
                bounced_visits=metrics_data['bounced_visits'],
                pageviews=metrics_data['pageviews'],
                duration=metrics_data['duration']
            )
            raw_postclick_stats.save()

            for goal_name, conversion_metrics in metrics_data.get('goals', {}).items():
                raw_goal_stats = RawGoalConversionStats(
                    datetime=dt,
                    ad_group_id=int(landing_page.ad_group_id),
                    source_id=source_id,
                    goal_name=goal_name,
                    url_raw=landing_page.raw_url,
                    url_clean=landing_page.clean_url,
                    device_type=entry['Device Category'],
                    z1_adgid=str(landing_page.ad_group_id),
                    z1_msid=landing_page.source_param,
                    z1_did=landing_page.z1_did,
                    z1_kid=landing_page.z1_kid,
                    z1_tid=landing_page.z1_tid,
                    conversions=conversion_metrics['conversions'],
                    conversions_value_cc=conversion_metrics['conversions_value_cc'],
                )
                raw_goal_stats.save()

    # def store_to_s3(self):
    #     ext = mimetypes.guess_extension(self.report.get_content_type())
    #     key = S3_REPORT_KEY_FORMAT.format(
    #         sender=self.sender,
    #         date=self.report.get_date(),
    #         ts=datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S'),
    #         ext=ext if ext else ''
    #     )

    #     try:
    #         utils.s3helpers.S3Helper().put(key, self.report.raw)
    #     except Exception:
    #         logger.exception('Error while saving conversion report to s3')
