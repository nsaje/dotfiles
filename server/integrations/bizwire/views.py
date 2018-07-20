from collections import OrderedDict
import logging
from functools import partial
import json
import re
import urllib.request, urllib.error, urllib.parse

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
from utils import request_signer, threads


logger = logging.getLogger(__name__)

CACHE_KEY_FMT = "bizwire_promotion_export_{}"
VALID_US_STATES = [
    "US-AK",
    "US-AL",
    "US-AR",
    "US-AZ",
    "US-CA",
    "US-CO",
    "US-CT",
    "US-DE",
    "US-FL",
    "US-GA",
    "US-HI",
    "US-IA",
    "US-ID",
    "US-IL",
    "US-IN",
    "US-KS",
    "US-KY",
    "US-LA",
    "US-MA",
    "US-MD",
    "US-ME",
    "US-MI",
    "US-MN",
    "US-MO",
    "US-MS",
    "US-MT",
    "US-NC",
    "US-ND",
    "US-NE",
    "US-NH",
    "US-NJ",
    "US-NM",
    "US-NV",
    "US-NY",
    "US-OH",
    "US-OK",
    "US-OR",
    "US-PA",
    "US-RI",
    "US-SC",
    "US-SD",
    "US-TN",
    "US-TX",
    "US-UT",
    "US-VA",
    "US-VT",
    "US-WA",
    "US-WI",
    "US-WV",
    "US-WY",
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
            logger.exception("Invalid signature.")
            raise Http404

    @staticmethod
    def response_ok(content):
        return JsonResponse({"error": None, "response": content})

    @staticmethod
    def response_error(msg, status=400):
        return JsonResponse({"error": msg, "response": None}, status=status)


class PromotionExport(RatelimitMixin, BizwireView):
    ratelimit_key = "ip"
    ratelimit_rate = "30/s"
    ratelimit_block = True
    ratelimit_method = "GET"

    def _get_geo_stats(self, content_ads):
        return db.execute_query(
            backtosql.generate_sql(
                "bizwire_geo.sql", {"content_ad_ids": [content_ad.id for content_ad in content_ads]}
            ),
            [],
            "bizwire_geo",
        )

    def _get_pubs_stats(self, ad_group_id):
        return db.execute_query(backtosql.generate_sql("bizwire_pubs.sql", {}), [ad_group_id], "bizwire_pubs")

    def _get_ad_stats(self, content_ads):
        return db.execute_query(
            backtosql.generate_sql(
                "bizwire_ad_stats.sql",
                {
                    "ctr": backtosql.TemplateColumn(
                        "part_sumdiv_perc.sql", {"expr": "clicks", "divisor": "impressions"}
                    ),
                    "content_ad_ids": [content_ad.id for content_ad in content_ads],
                },
            ),
            [],
            "bizwire_ad_stats",
        )[0]

    # def _get_ag_stats(self, ad_group_id):
    #     return db.execute_query(
    #         backtosql.generate_sql('bizwire_ag_stats.sql', {
    #             'industry_ctr': backtosql.TemplateColumn(
    #                 'part_sumdiv_perc.sql',
    #                 {'expr': 'clicks', 'divisor': 'impressions'}
    #             )
    #         }),
    #         [ad_group_id],
    #         'bizwire_ag_stats'
    #     )[0]

    def _get_state_key(self, state):
        if not state or state not in VALID_US_STATES:
            return "Unknown"

        return state

    def _get_statistics(self, content_ads):
        ad_stats_thread = threads.AsyncFunction(partial(self._get_ad_stats, content_ads))
        ad_stats_thread.start()

        # ag_stats_thread = threads.AsyncFunction(partial(self._get_ag_stats, content_ad.ad_group_id))
        # ag_stats_thread.start()

        pubs_thread = threads.AsyncFunction(partial(self._get_pubs_stats, content_ads[0].ad_group_id))
        pubs_thread.start()

        geo_impressions_thread = threads.AsyncFunction(partial(self._get_geo_stats, content_ads))
        geo_impressions_thread.start()

        ad_stats = ad_stats_thread.join_and_get_result()
        # ag_stats = ag_stats_thread.join_and_get_result()
        pubs_stats = pubs_thread.join_and_get_result()
        geo_stats = geo_impressions_thread.join_and_get_result()

        geo_impressions = OrderedDict()
        for row in geo_stats:
            key = self._get_state_key(row["state"])
            geo_impressions.setdefault(key, 0)
            geo_impressions[key] += row["impressions"]

        pubs = [row["publisher"] for row in pubs_stats]

        return {
            "headline_impressions": ad_stats["impressions"] or 0,
            "release_views": ad_stats["clicks"] or 0,
            "ctr": ad_stats["ctr"] or None,
            "industry_ctr": 0.17,  # ag_stats['industry_ctr'] or None,
            "publishers": pubs,
            "geo_headline_impressions": geo_impressions,
        }

    @influx.timer("integrations.bizwire.views.promotion_export")
    def get(self, request):
        article_id = request.GET.get("article_id")
        article_url = request.GET.get("article_url")
        if article_url:
            m = re.search("news/home/([^/]+)/", urllib.parse.unquote(article_url))
            if m:
                article_id = m.groups()[0]

        cache = caches["bizwire_cache"]
        cache_key = CACHE_KEY_FMT.format(article_id)
        cached_response = cache.get(cache_key)
        if cached_response:
            return self.response_ok(json.loads(cached_response))

        # NOTE: it is possible in rare situations for a single article to get inserted multiple times and
        # this is handled here by using filter instead of get
        content_ads = dash.models.ContentAd.objects.filter(
            label=article_id, ad_group__campaign_id=config.AUTOMATION_CAMPAIGN
        )
        if not content_ads:
            return self.response_error("Article not found", status=404)

        response = {
            "article": {"title": content_ads[0].title, "description": content_ads[0].description},
            "statistics": self._get_statistics(content_ads),
        }

        cache.set(cache_key, json.dumps(response))
        return self.response_ok(response)
