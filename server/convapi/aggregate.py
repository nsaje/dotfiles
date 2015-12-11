import logging

import exc
from constants import ALLOWED_ERRORS_COUNT
from models import RawPostclickStats, RawGoalConversionStats
from resolve import resolve_source, resolve_article
from convapi import constants as convapi_constants

import dash.models
import reports.models
import reports.update
import reports.refresh
from utils import statsd_helper

logger = logging.getLogger(__name__)

# special source param designating url's from zemanta dashboard
Z1_SOURCE_PARAM = 'z1'


class ReportEmail(object):

    def __init__(self, sender, recipient, subject, date, text, report, report_log):
        self.sender = sender
        self.recipient = recipient
        self.subject = subject
        self.text = text
        self.date = date
        self.report = report
        self.report_log = report_log

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
        visits = int(entry['Sessions'].replace(',', ''))
        data['visits'] += visits
        data['new_visits'] += int(entry['New Users'].replace(',', ''))
        data['bounced_visits'] += int(round(float(
            entry['Bounce Rate'].replace('%', '').replace(',', '')) / 100 * visits))
        data['pageviews'] += int(round(float(entry['Pages / Session']) * visits))
        data['duration'] += visits * self._parse_duration(entry['Avg. Session Duration'])
        for goal_name, metric_fields in goal_fields.items():
            data['goals'][goal_name]['conversions'] += int(
                entry[metric_fields['conversions']].replace(',', ''))
            conv_value = self._parse_conversion_value(entry[metric_fields['value']])
            data['goals'][goal_name]['conversions_value_cc'] += int(10000 * conv_value)

    def _parse_conversion_value(self, conv_val_str):
        for i, c in enumerate(conv_val_str):
            if c.isdigit():
                break
        conv_val_str = conv_val_str[i:].replace(',', '')
        return float(conv_val_str)

    def get_stats_by_key(self):

        goal_fields = self.get_goal_fields()

        stats = {}

        source_resolve_lookup = {}
        article_resolve_lookup = {}

        errors_count = 0
        for entry in self.report.get_entries():
            identifier = self.report.get_identifier_object(entry)

            if identifier.source_param == Z1_SOURCE_PARAM:
                logger.warning('ERROR: Not resolving z1 dashboard source for (ad_group=%s, sender=%s,\
recipient=%s, subject=%s, maildate=%s, \
landing_page_url=%s',
                    identifier.ad_group_id,
                    self.sender,
                    self.recipient,
                    self.subject,
                    self.date,
                    identifier.id.decode('ascii', 'ignore')
                )
                self.report_log.add_error(
                    'Not resolving z1 dashboard source for url=%s' % identifier.id.decode('ascii', 'ignore'))
                continue

            if identifier.source_param not in source_resolve_lookup:
                source_resolve_lookup[identifier.source_param] = resolve_source(identifier.source_param)
            source = source_resolve_lookup[identifier.source_param]

            if source is None:
                errors_count += 1
                logger.warning('ERROR: Cannot resolve source for (ad_group=%s, sender=%s,\
recipient=%s, subject=%s, maildate=%s, \
landing_page_url=%s',
                    identifier.ad_group_id,
                    self.sender,
                    self.recipient,
                    self.subject,
                    self.date,
                    identifier.id.decode('ascii', 'ignore')
                )
                self.report_log.add_error(
                    'Cannot resolve source for url=%s' % identifier.id.decode('ascii', 'ignore'))
                if errors_count > ALLOWED_ERRORS_COUNT:
                    self.report_log.state = convapi_constants.ReportState.FAILED
                    self.report_log.add_error(
                        'There are too many errors in urls. Adgroup or sources missing in GA report.')
                    self.report_log.save()
                    raise exc.TooManyMissingSourcesException(
                        "There are too many sources missing in GA report.")
                else:
                    continue

            if identifier.id not in article_resolve_lookup:
                article_resolve_lookup[identifier.id] = resolve_article(
                    identifier.url, identifier.ad_group_id, self.report.get_date(), source, self.report_log)
            article = article_resolve_lookup[identifier.id]
            if article is None:
                logger.warning('ERROR: Cannot resolve article for (ad_group=%s, sender=%s,\
recipient=%s, subject=%s, maildate=%s, \
landing_page_url=%s',
                    identifier.ad_group_id,
                    self.sender,
                    self.recipient,
                    self.subject,
                    self.date,
                    identifier.id.decode('ascii', 'ignore')
                 )
                self.report_log.add_error('Cannot resolve article for identifier=%s' % identifier.id.decode('ascii', 'ignore'))
                continue

            key = (self.report.get_date(), article.id, identifier.ad_group_id, source.id)

            data = stats.get(key, self.get_initial_data(goal_fields))

            self.add_parsed_metrics(data, entry, goal_fields)

            stats[key] = data

        return stats

    def _parse_duration(self, durstr):
        hours_str, minutes_str, seconds_str = durstr.replace('<', '').split(':')
        return int(seconds_str) + 60 * int(minutes_str) + 60 * 60 * int(hours_str)

    @statsd_helper.statsd_timer('convapi', 'aggregate')
    def aggregate(self):
        data = self.get_stats_by_key()

        if not len(data):
            return

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

        stat_rows = []
        conv_rows = []
        ad_group_id_set = set()
        date_set = set()

        article_ids = source_ids = set()
        for (dt, article_id, ad_group_id, source_id), statvals in data.iteritems():
            source_ids.add(source_id)
            article_ids.add(article_id)

        articles = dash.models.Article.objects.filter(id__in=article_ids).all()
        sources = dash.models.Source.objects.filter(id__in=source_ids).all()
        logger.info("Aggregating ReportMail for %d articles on %d sources", len(articles), len(sources))

        for (dt, article_id, ad_group_id, source_id), statvals in data.iteritems():
            ad_group_id_set.add(ad_group_id)
            date_set.add(dt)

            article = articles.get(id=article_id)
            source = sources.get(id=source_id)

            stat_rows.append({
                'article': article,
                'source': source,
                'visits': statvals['visits'],
                'new_visits': statvals['new_visits'],
                'bounced_visits': statvals['bounced_visits'],
                'pageviews': statvals['pageviews'],
                'duration': statvals['duration']
            })

            for goal_name, goal_stats in statvals['goals'].iteritems():
                conv_rows.append({
                    'article': article,
                    'source': source,
                    'goal_name': goal_name,
                    'conversions': goal_stats['conversions'],
                    'conversions_value_cc': goal_stats['conversions_value_cc']
                })

        assert len(ad_group_id_set) == 1
        assert len(date_set) == 1

        dt = list(date_set)[0]
        ad_group = dash.models.AdGroup.objects.get(id=list(ad_group_id_set)[0])
        logger.info("\tGA-aggregate - stats_update_adgroup_postclick - before")
        reports.update.stats_update_adgroup_postclick(
            datetime=dt,
            ad_group=ad_group,
            rows=stat_rows
        )
        logger.info("\tGA-aggregate - stats_update_adgroup_postclick - after")
        logger.info("\tGA-aggregate - goals_update_adgroup - before")
        reports.update.goals_update_adgroup(
            datetime=dt,
            ad_group=ad_group,
            rows=conv_rows
        )
        reports.refresh.notify_contentadstats_change(dt, ad_group.campaign_id)
        logger.info("\tGA-aggregate - goals_update_adgroup - after")
        logger.info("\tGA-aggregate - add_visits_imported - before")
        self.report_log.add_visits_imported(sum(d['visits'] for d in data.values()))
        logger.info("\tGA-aggregate - add_visits_imported - after")

    @statsd_helper.statsd_timer('convapi', 'save_raw')
    def save_raw(self):
        goal_fields = self.get_goal_fields()
        dt = self.report.get_date()

        entries = self.report.get_entries()

        identifier = self.report.get_identifier_object(entries[0])
        ad_group_id = identifier.ad_group_id

        if ad_group_id is None:
            logger.warning(
                'Cannot handle identifier with no ad_group_id %s',
                identifier.id.decode('ascii', 'ignore'))
            return

        RawPostclickStats.objects.filter(datetime=dt, ad_group_id=ad_group_id).delete()
        RawGoalConversionStats.objects.filter(datetime=dt, ad_group_id=ad_group_id).delete()

        n_visits = 0
        for entry in entries:
            identifier = self.report.get_identifier_object(entry)

            assert identifier.ad_group_id == ad_group_id
            assert ad_group_id is not None

            if identifier.source_param is None:
                continue

            source = resolve_source(identifier.source_param)

            source_id = source.id if source is not None else None

            metrics_data = self.get_initial_data(goal_fields)
            self.add_parsed_metrics(metrics_data, entry, goal_fields)

            n_visits += metrics_data['visits']

            raw_postclick_stats = RawPostclickStats(
                datetime=dt,
                url_raw=identifier.id,
                url_clean=identifier.url,
                ad_group_id=int(identifier.ad_group_id),
                source_id=source_id,
                device_type=entry.get('Device Category'),
                z1_adgid=str(identifier.ad_group_id)[:32],
                z1_msid=str(identifier.source_param)[:64],
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
                    ad_group_id=int(identifier.ad_group_id),
                    source_id=source_id,
                    goal_name=goal_name,
                    url_raw=identifier.id,
                    url_clean=identifier.url,
                    device_type=entry.get('Device Category'),
                    z1_adgid=str(identifier.ad_group_id)[:32],
                    z1_msid=str(identifier.source_param)[:64],
                    conversions=conversion_metrics['conversions'],
                    conversions_value_cc=conversion_metrics['conversions_value_cc'],
                )
                raw_goal_stats.save()

        self.report_log.add_visits_reported(n_visits)
