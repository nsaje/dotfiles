import logging
import datetime
import uuid

from django.conf import settings

import dash.constants
import dash.models
from utils import db_for_reads
import redshiftapi.api_quickstats
import redshiftapi.internal_stats.conversions
import redshiftapi.internal_stats.content_ad_publishers
import etl.s3
import dash.features.custom_flags

from .base import K1APIView

logger = logging.getLogger(__name__)


class AdGroupStatsView(K1APIView):
    """
    Returns quickstats for an adgroup (used for decision making based on whether the ad group has spent already)
    """

    @db_for_reads.use_read_replica()
    def get(self, request):
        ad_group_id = request.GET.get("ad_group_id")
        source_slug = request.GET.get("source_slug")
        ad_group = dash.models.AdGroup.objects.get(pk=ad_group_id)
        try:
            source = dash.models.Source.objects.get(bidder_slug=source_slug)
        except dash.models.Source.DoesNotExist:
            return self.response_error("Source '{}' does not exist".format(source_slug), status=400)
        from_date = ad_group.created_dt.date()
        to_date = datetime.date.today() + datetime.timedelta(days=1)
        stats = redshiftapi.api_quickstats.query_adgroup(ad_group.id, from_date, to_date, source.id)
        return self.response_ok(
            {
                "total_cost": stats["total_cost"],
                "impressions": stats["impressions"],
                "clicks": stats["clicks"],
                "cpc": stats["cpc"],
            }
        )


class AdGroupConversionStatsView(K1APIView):
    """
    Returns conversion stats for an adgroup (used for post kpi optimization in bidder)
    """

    def get(self, request):
        try:
            from_date = datetime.datetime.strptime(request.GET.get("from_date"), "%Y-%m-%d").date()
            to_date = datetime.datetime.strptime(request.GET.get("to_date"), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return self.response_error("Invalid date format", status=400)

        ad_group_ids = request.GET.get("ad_group_ids")
        if ad_group_ids:
            ad_group_ids = ad_group_ids.split(",")

        path = etl.s3.upload_csv(
            "conversions",
            from_date,
            uuid.uuid4().hex,
            lambda: redshiftapi.internal_stats.conversions.query_conversions(from_date, to_date, ad_group_ids),
        )

        return self.response_ok({"path": path, "bucket": settings.S3_BUCKET_STATS})


class AdGroupContentAdPublisherStatsView(K1APIView):
    """
    Returns conversion stats for an adgroup (used for post kpi optimization in bidder)
    """

    def get(self, request):
        try:
            from_date = datetime.datetime.strptime(request.GET.get("from_date"), "%Y-%m-%d").date()
            to_date = datetime.datetime.strptime(request.GET.get("to_date"), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return self.response_error("Invalid date format", status=400)

        ad_group_ids = request.GET.get("ad_group_ids")
        if ad_group_ids:
            ad_group_ids = ad_group_ids.split(",")

        min_media_cost = request.GET.get("min_media_cost")
        if min_media_cost:
            min_media_cost = float(min_media_cost)

        _, path = etl.s3.upload_csv_async(
            "content_ad_publishers",
            from_date,
            uuid.uuid4().hex,
            lambda: redshiftapi.internal_stats.content_ad_publishers.query_content_ad_publishers(
                from_date, to_date, ad_group_ids, min_media_cost
            ),
        )

        return self.response_ok({"path": path, "bucket": settings.S3_BUCKET_STATS})
