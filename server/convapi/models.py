import logging

from parse import LandingPageUrl
from resolve import resolve_source, resolve_article

import dash.models
import reports.models


logger = logging.getLogger(__name__)


class ReportEmail(object):
    
    def __init__(self, sender, recipient, subject, date, text, report):
        self.sender = sender
        self.recipient = recipient
        self.subject = subject
        self.text = text
        self.date = date
        self.report = report
        
    def is_ad_group_consistent(self):
        ad_group_set = set()
        try:
            for entry in self.report.get_entries():
                url = LandingPageUrl(entry['Landing Page'])
                ad_group_set.add(url.ad_group_id)
            return len(ad_group_set) == 1
        except:
            return False
            
    def is_media_source_specified(self):
        # check if the media source parameter is defined for each landing page url
        try:
            for entry in self.report.get_entries():
                url = LandingPageUrl(entry['Landing Page'])
                if url.source_param is None:
                    return False
        except:
            return False
        return True
        
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

    def get_stats_by_key(self):

        goal_fields = self.get_goal_fields()

        def get_initial_goal_data():
            data = {}
            for goal_name in goal_fields:
                data[goal_name] = {'conversions': 0, 'conversions_value_cc': 0}
            return data

        stats = {}

        
        for entry in self.report.get_entries():
            url = LandingPageUrl(entry['Landing Page'])
            try:
                source = resolve_source(url.source_param)
                if source is None: raise
            except:
                logger.error('ERROR: Cannot resolve source for (ad_group={ad_group}, sender={sender},\
recipient={recipient}, subject={subject}, maildate={maildate}, \
landing_page_url={landing_page_url})'.format(
                    ad_group=url.ad_group_id,
                    sender=self.sender,
                    recipient=self.recipient,
                    subject=self.subject,
                    maildate=self.date,
                    landing_page_url=url.raw_url
                 ))
                continue
            try:
                article = resolve_article(url.clean_url, url.ad_group_id, self.report.get_date(), source)
                if article is None: raise
            except:
                logger.error('ERROR: Cannot resolve article for (ad_group={ad_group}, sender={sender},\
recipient={recipient}, subject={subject}, maildate={maildate}, \
landing_page_url={landing_page_url})'.format(
                    ad_group=url.ad_group_id,
                    sender=self.sender,
                    recipient=self.recipient,
                    subject=self.subject,
                    maildate=self.date,
                    landing_page_url=url.raw_url
                 ))
                continue
            key = (self.report.get_date(), article.id, url.ad_group_id, source.id)
            data = stats.get(key, {
                    'visits': 0,
                    'new_visits': 0,
                    'bounced_visits': 0,
                    'pageviews': 0,
                    'duration': 0,
                    'goals': get_initial_goal_data(),
                })

            
            visits = int(entry['Sessions'])
            data['visits'] += visits
            data['new_visits'] += int(entry['New Users'])
            data['bounced_visits'] += int(round(float(entry['Bounce Rate'].replace('%', '')) / 100 * visits))
            data['pageviews'] += int(round(float(entry['Pages / Session']) * visits))
            data['duration'] += visits * self._parse_duration(entry['Avg. Session Duration'])
            for goal_name, metric_fields in goal_fields.items():
                data['goals'][goal_name]['conversions'] += int(entry[metric_fields['conversions']])

            stats[key] = data

        return stats

    def _parse_duration(self, durstr):
        hours_str, minutes_str, seconds_str = durstr.replace('<', '').split(':')
        return int(seconds_str) + 60*int(minutes_str) + 60*60*int(hours_str)

    def aggregate(self):
        data = self.get_stats_by_key()

        logger.info('Aggregating report email ( \
sender={sender}, recipient={recipient}, \
subject={subject}, maildate={maildate} \
) with total values of (visits={visits}, new_visits={new_visits}, \
bounced_visits={bounced_visits}, pageviews={pageviews}, duration={duration})'.format(
            sender=self.sender,
            recipient=self.recipient,
            subject=self.subject,
            maildate=self.date,
            visits=sum(d['visits'] for d in data.values()),
            new_visits=sum(d['new_visits'] for d in data.values()),
            bounced_visits=sum(d['bounced_visits'] for d in data.values()),
            pageviews=sum(d['pageviews'] for d in data.values()),
            duration=sum(d['duration'] for d in data.values())
        ))

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
            article_stats.reset_postclick_metrics()
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
