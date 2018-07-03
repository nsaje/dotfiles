import logging

from django.db import transaction

import dash.constants
import dash.models
from dash import constants
from utils import redirector_helper
from utils import db_for_reads

from .base import K1APIView

logger = logging.getLogger(__name__)


class SourcesView(K1APIView):

    @db_for_reads.use_read_replica()
    def get(self, request):
        source_slugs = request.GET.get("source_slugs")
        sources = dash.models.Source.objects.all().select_related('defaultsourcesettings',
                                                                  'defaultsourcesettings__credentials')
        if source_slugs:
            sources = sources.filter(bidder_slug__in=source_slugs.split(','))

        response = []
        for source in sources:
            source_dict = {
                'id': source.id,
                'name': source.name,
                'slug': source.tracking_slug,
                'credentials': None
            }
            try:
                default_credentials = source.defaultsourcesettings.credentials
                if default_credentials:
                    source_dict['credentials'] = {
                        'id': default_credentials.id,
                        'credentials': default_credentials.credentials
                    }
            except dash.models.DefaultSourceSettings.DoesNotExist:
                pass
            response.append(source_dict)
        return self.response_ok(response)


class SourcePixelsView(K1APIView):

    @transaction.atomic
    def put(self, request):
        data = request.data
        pixel_id = data['pixel_id']
        source_type = data['source_type']

        conversion_pixel = dash.models.ConversionPixel.objects.get(id=pixel_id)

        if source_type == 'outbrain':
            self._update_outbrain_pixel(conversion_pixel.account, data)
        else:
            self._create_source_pixel(conversion_pixel, source_type, data)
            self._propagate_pixels_to_r1(pixel_id)

        return self.response_ok(data)

    def _propagate_pixels_to_r1(self, pixel_id):
        audiences = dash.models.Audience.objects.filter(pixel_id=pixel_id, archived=False)

        for audience in audiences:
            redirector_helper.upsert_audience(audience)

    def _create_source_pixel(self, conversion_pixel, source_type, data):
        source_pixel, created = dash.models.SourceTypePixel.objects.get_or_create(
            pixel__id=conversion_pixel.id,
            source_type__type=source_type,
            defaults={
                'pixel': conversion_pixel,
                'source_type': dash.models.SourceType.objects.get(type=source_type),
            })

        source_pixel.url = data['url']
        source_pixel.source_pixel_id = data['source_pixel_id']
        source_pixel.save()

    def _update_outbrain_pixel(self, account, data):
        pixels = dash.models.ConversionPixel.objects.\
            filter(account_id=account.id).\
            filter(audience_enabled=True)
        if not pixels:
            return

        if len(pixels) > 1:
            msg = 'More than 1 pixel enabled for audience building for account {}'.format(account.id)
            return self.response_error(msg)

        conversion_pixel = pixels[0]
        r1_pixels_to_sync = []

        source_type_pixels = dash.models.SourceTypePixel.objects.filter(
            pixel__account=account, source_type__type=constants.SourceType.OUTBRAIN
        )
        if len(source_type_pixels) > 1:
            return self.response_error('More than 1 outbrain source type pixel for account {}'.format(account.id))

        if not source_type_pixels:
            self._create_source_pixel(conversion_pixel, 'outbrain', data)
            r1_pixels_to_sync.append(conversion_pixel.id)
        elif source_type_pixels[0].pixel != conversion_pixel:
            r1_pixels_to_sync.append(conversion_pixel.id)
            r1_pixels_to_sync.append(source_type_pixels[0].pixel.id)

            source_type_pixels[0].pixel = conversion_pixel
            source_type_pixels[0].save()

        # sync all audiences on edited pixels with R1
        for pixel_id in r1_pixels_to_sync:
            self._propagate_pixels_to_r1(pixel_id)
