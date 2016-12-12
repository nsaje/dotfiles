from collections import OrderedDict
import logging
from functools import partial
import json
import re
import urllib2

import influx
from ratelimit.mixins import RatelimitMixin

from django.core.cache import caches
from django.conf import settings
from django.http import JsonResponse, Http404
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

import backtosql
from redshiftapi import db
from . import config

import dash.models
from dash import threads
from utils import request_signer


logger = logging.getLogger(__name__)

CACHE_KEY_FMT = 'bizwire_promotion_export_{}'
MOCK_RESPONSE = {
    'article': {
        'title': 'Title comes here',
        'description': 'Description comes here'
    },
    'statistics': {
        'headline_impressions': 123,
        'release_views': 123,
        'ctr': 0.01,
        'industry_ctr': 0.01,
        'publishers': [
            'example.com',
            'second-example.com',
            'third-example.com'
        ],
        'geo_headline_impressions': {
            'US-AL': 1,
            'US-AK': 2,
            'US-AZ': 3,
            'US-AR': 4
        }
    }
}

VALID_US_STATES = [
    'AK', 'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'IA', 'ID', 'IL', 'IN', 'KS', 'KY', 'LA', 'MA',
    'MD', 'ME', 'MI', 'MN', 'MO', 'MS', 'MT', 'NC', 'ND', 'NE', 'NH', 'NJ', 'NM', 'NV', 'NY', 'OH', 'OK', 'OR', 'PA',
    'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VA', 'VT', 'WA', 'WI', 'WV', 'WY',
]


class BizwireView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        self._validate_signature(request)
        return super(BizwireView, self).dispatch(request, *args, **kwargs)

    @staticmethod
    def _validate_signature(request):
        try:
            request_signer.verify_wsgi_request(request, settings.BIZWIRE_API_SIGN_KEY)
        except request_signer.SignatureError:
            logger.exception('Invalid signature.')
            raise Http404

    @staticmethod
    def response_ok(content):
        return JsonResponse({
            'error': None,
            'response': content,
        })

    @staticmethod
    def response_error(msg, status=400):
        return JsonResponse({
            'error': msg,
            'response': None,
        }, status=status)


class PromotionExport(RatelimitMixin, BizwireView):
    ratelimit_key = 'ip'
    ratelimit_rate = '30/s'
    ratelimit_block = True
    ratelimit_method = 'GET'

    def _get_geo_stats(self, content_ad_id):
        return db.execute_query(
            backtosql.generate_sql('bizwire_geo.sql', {}),
            [content_ad_id],
            'bizwire_geo'
        )

    def _get_pubs_stats(self, ad_group_id):
        return db.execute_query(
            backtosql.generate_sql('bizwire_pubs.sql', {}),
            [ad_group_id],
            'bizwire_pubs'
        )

    def _get_ad_stats(self, content_ad_id):
        return db.execute_query(
            backtosql.generate_sql('bizwire_ad_stats.sql', {
                'ctr': backtosql.TemplateColumn(
                    'part_sumdiv_perc.sql',
                    {'expr': 'clicks', 'divisor': 'impressions'}
                )
            }),
            [content_ad_id],
            'bizwire_ad_stats'
        )[0]

    def _get_ag_stats(self, ad_group_id):
        return db.execute_query(
            backtosql.generate_sql('bizwire_ag_stats.sql', {
                'industry_ctr': backtosql.TemplateColumn(
                    'part_sumdiv_perc.sql',
                    {'expr': 'clicks', 'divisor': 'impressions'}
                )
            }),
            [ad_group_id],
            'bizwire_ag_stats'
        )[0]

    def _get_state_key(self, country, state):
        if not country or not state or state not in VALID_US_STATES:
            return 'Unknown'

        return country + '-' + state

    def _get_statistics(self, content_ad):
        ad_stats_thread = threads.AsyncFunction(partial(self._get_ad_stats, content_ad.id))
        ad_stats_thread.start()

        # ag_stats_thread = threads.AsyncFunction(partial(self._get_ag_stats, content_ad.ad_group_id))
        # ag_stats_thread.start()

        pubs_thread = threads.AsyncFunction(partial(self._get_pubs_stats, content_ad.ad_group_id))
        pubs_thread.start()

        geo_impressions_thread = threads.AsyncFunction(partial(self._get_geo_stats, content_ad.id))
        geo_impressions_thread.start()

        ad_stats = ad_stats_thread.join_and_get_result()
        # ag_stats = ag_stats_thread.join_and_get_result()
        pubs_stats = pubs_thread.join_and_get_result()
        geo_stats = geo_impressions_thread.join_and_get_result()

        geo_impressions = OrderedDict()
        for row in geo_stats:
            key = self._get_state_key(row['country'], row['state'])
            geo_impressions.setdefault(key, 0)
            geo_impressions[key] += row['impressions']

        pubs = [row['publisher'] for row in pubs_stats]

        return {
            'headline_impressions': ad_stats['impressions'] or 0,
            'release_views': ad_stats['clicks'] or 0,
            'ctr': ad_stats['ctr'] or None,
            'industry_ctr': 0.17,
            'publishers': pubs,
            'geo_headline_impressions': geo_impressions,
        }

    @influx.timer('integrations.bizwire.views.promotion_export')
    def get(self, request):
        article_id = request.GET.get('article_id')
        article_url = request.GET.get('article_url')
        if article_url:
            m = re.search('news/home/([^/]+)/', urllib2.unquote(article_url))
            if m:
                article_id = m.groups()[0]

        cache = caches['bizwire_cache']
        cache_key = CACHE_KEY_FMT.format(article_id)
        cached_response = cache.get(cache_key)
        if cached_response:
            return self.response_ok(json.loads(cached_response))

        try:
            content_ad = dash.models.ContentAd.objects.get(
                label=article_id,
                ad_group__campaign_id=config.AUTOMATION_CAMPAIGN,
            )
        except dash.models.ContentAd.DoesNotExist:
            return self.response_error('Article not found', status=404)

        if content_ad.ad_group_id == config.TEST_FEED_AD_GROUP:
            return self.response_ok(MOCK_RESPONSE)

        response = {
            'article': {
                'title': content_ad.title,
                'description': content_ad.description,
            },
            'statistics': self._get_statistics(content_ad),
        }

        cache.set(cache_key, json.dumps(response))
        return self.response_ok(response)
