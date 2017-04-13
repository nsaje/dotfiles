# -*- coding: utf-8 -*-
import urlparse

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models

import utils.demo_anonymizer
import utils.string_helper
from dash import constants
from dash import image_helper

import core.common
import core.entity
import core.history
import core.source


class ContentAd(models.Model):
    class Meta:
        get_latest_by = 'created_dt'
        app_label = 'dash'

    _demo_fields = {
        'url': utils.demo_anonymizer.fake_content_ad_url,
        'display_url': utils.demo_anonymizer.fake_display_url,
        'brand_name': utils.demo_anonymizer.fake_brand,
        'redirect_id': lambda: 'u1jvpq0wthxc',
        'tracker_urls': [],
    }

    label = models.CharField(max_length=100, default='')
    url = models.CharField(max_length=2048, editable=False)
    title = models.CharField(max_length=256, editable=False)
    display_url = models.CharField(max_length=25, blank=True, default='')
    brand_name = models.CharField(max_length=25, blank=True, default='')
    description = models.CharField(max_length=140, blank=True, default='')
    call_to_action = models.CharField(max_length=25, blank=True, default='')

    ad_group = models.ForeignKey('AdGroup', on_delete=models.PROTECT)
    batch = models.ForeignKey('UploadBatch', on_delete=models.PROTECT)
    sources = models.ManyToManyField(core.source.Source, through='ContentAdSource')

    image_id = models.CharField(max_length=256, editable=False, null=True)
    image_width = models.PositiveIntegerField(null=True)
    image_height = models.PositiveIntegerField(null=True)
    image_hash = models.CharField(max_length=128, null=True)
    crop_areas = models.CharField(max_length=128, null=True)
    image_crop = models.CharField(
        max_length=25, default=constants.ImageCrop.CENTER)

    redirect_id = models.CharField(max_length=128, null=True)

    created_dt = models.DateTimeField(
        auto_now_add=True, verbose_name='Created at')

    state = models.IntegerField(
        null=True,
        default=constants.ContentAdSourceState.ACTIVE,
        choices=constants.ContentAdSourceState.get_choices()
    )

    archived = models.BooleanField(default=False)
    tracker_urls = ArrayField(models.CharField(max_length=2048), null=True)

    objects = core.common.QuerySetManager()

    def get_original_image_url(self, width=None, height=None):
        if self.image_id is None:
            return None

        return urlparse.urljoin(settings.IMAGE_THUMBNAIL_URL, '{image_id}.jpg'.format(
            image_id=self.image_id
        ))

    def get_image_url(self, width=None, height=None):
        if width is None:
            width = self.image_width

        if height is None:
            height = self.image_height

        return image_helper.get_image_url(self.image_id, width, height, self.image_crop)

    def url_with_tracking_codes(self, tracking_codes):
        if not tracking_codes:
            return self.url

        parsed = list(urlparse.urlparse(self.url))

        parts = []
        if parsed[4]:
            parts.append(parsed[4])
        parts.append(tracking_codes)

        parsed[4] = '&'.join(parts)

        return urlparse.urlunparse(parsed)

    def get_url(self, ad_group):
        return self.url

    def get_redirector_url(self):
        return settings.R1_BLANK_REDIRECT_URL.format(
            redirect_id=self.redirect_id,
            content_ad_id=self.id
        )

    def __unicode__(self):
        return '{cn}(id={id}, ad_group={ad_group}, image_id={image_id}, state={state})'.format(
            cn=self.__class__.__name__,
            id=self.id,
            ad_group=self.ad_group,
            image_id=self.image_id,
            state=self.state,
        )

    def __str__(self):
        return unicode(self).encode('ascii', 'ignore')

    def to_candidate_dict(self):
        return {
            'label': self.label,
            'url': self.url,
            'title': self.title,
            'image_url': self.get_image_url(),
            'image_id': self.image_id,
            'image_hash': self.image_hash,
            'image_width': self.image_width,
            'image_height': self.image_height,
            'image_crop': self.image_crop,
            'display_url': self.display_url,
            'description': self.description,
            'brand_name': self.brand_name,
            'call_to_action': self.call_to_action,
            'primary_tracker_url': self.tracker_urls[0] if self.tracker_urls else None,
            'secondary_tracker_url': self.tracker_urls[1] if self.tracker_urls and len(self.tracker_urls) > 1 else None,
        }

    class QuerySet(models.QuerySet):

        def filter_by_user(self, user):
            return self.filter(
                models.Q(ad_group__campaign__users__id=user.id) |
                models.Q(ad_group__campaign__groups__user__id=user.id) |
                models.Q(ad_group__campaign__account__users__id=user.id) |
                models.Q(ad_group__campaign__account__groups__user__id=user.id) |
                models.Q(ad_group__campaign__account__agency__users__id=user.id)
            ).distinct()

        def filter_by_sources(self, sources):
            if not core.entity.helpers.should_filter_by_sources(sources):
                return self

            content_ad_ids = core.entity.ContentAdSource.objects.filter(source__in=sources).select_related(
                'content_ad').distinct('content_ad_id').values_list('content_ad_id', flat=True)

            return self.filter(id__in=content_ad_ids)

        def exclude_archived(self, show_archived=False):
            if show_archived:
                return self

            return self.filter(archived=False)
