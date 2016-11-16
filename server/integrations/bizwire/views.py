from collections import OrderedDict
import logging
from functools import partial
import re

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


class PromotionExport(BizwireView):
    def _get_geo_impressions(self, content_ad_id):
        rows = db.execute_query(
            backtosql.generate_sql('bizwire_geo.sql', {}),
            [content_ad_id],
            'bizwire_geo'
        )

        geo_impressions = OrderedDict()
        for row in rows:
            key = (row['country'] + '-' + row['state']) if row['state'] else 'Unknown'
            geo_impressions.setdefault(key, 0)
            geo_impressions[key] += row['impressions']
        return geo_impressions

    def _get_pubs(self, content_ad_id):
        return map(
            lambda x: x['publisher'],
            db.execute_query(
                backtosql.generate_sql('bizwire_pubs.sql', {}),
                [content_ad_id],
                'bizwire_pubs'
            ),
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

    def _get_statistics(self, content_ad):
        ad_stats_thread = threads.AsyncFunction(partial(self._get_ad_stats, content_ad.id))
        ad_stats_thread.start()

        ag_stats_thread = threads.AsyncFunction(partial(self._get_ag_stats, content_ad.ad_group_id))
        ag_stats_thread.start()

        pubs_thread = threads.AsyncFunction(partial(self._get_pubs, content_ad.id))
        pubs_thread.start()

        geo_impressions_thread = threads.AsyncFunction(partial(self._get_geo_impressions, content_ad.id))
        geo_impressions_thread.start()

        ad_stats = ad_stats_thread.join_and_get_result()
        ag_stats = ag_stats_thread.join_and_get_result()
        pubs = pubs_thread.join_and_get_result()
        geo_impressions = geo_impressions_thread.join_and_get_result()

        return {
            'headline_impressions': ad_stats['impressions'] or 0,
            'release_views': ad_stats['clicks'] or 0,
            'ctr': ad_stats['ctr'] or None,
            'industry_ctr': ag_stats['industry_ctr'] or None,
            'publishers': pubs,
            'geo_headline_impressions': geo_impressions,
        }

    def get(self, request):
        article_id = request.GET.get('article_id')
        article_url = request.GET.get('article_url')
        if article_url:
            m = re.search('news/home/(\d*)/', article_url)
            if m and m.groups():
                article_id = m.groups()[0]

        try:
            content_ad = dash.models.ContentAd.objects.get(
                label=article_id,
                ad_group_id__in=config.TEST_AD_GROUP_IDS,
            )
        except dash.models.ContentAd.DoesNotExist:
            return self.response_ok(MOCK_RESPONSE)

        response = {
            'article': {
                'title': content_ad.title,
                'description': content_ad.description,
            },
            'statistics': self._get_statistics(content_ad),
        }
        return self.response_ok(response)
