# -*- coding: utf-8 -*-

from django.db import models
from django.db.models import Case
from django.db.models import Q
from django.db.models import When
from django.db.models.expressions import RawSQL

from dash import constants


class GeolocationQuerySet(models.QuerySet):
    def key_in(self, keys):
        return self.filter(key__in=keys)

    def of_type(self, types):
        return self.filter(type__in=types)

    def name_contains(self, query):
        return self.filter(name__unaccent__icontains=query).annotate(
            name_match_count=RawSQL("select count(*) from regexp_matches(lower(name), %s, 'g')", (query.lower(),))
        )


class GeolocationManager(models.Manager):
    def search(self, keys=None, types=None, name_contains=None, limit=None, offset=0):
        locations = (
            super(GeolocationManager, self)
            .get_queryset()
            .all()
            .annotate(
                num_external=(
                    Case(When(~Q(woeid=""), then=1), default=0, output_field=models.IntegerField())
                    + Case(When(~Q(outbrain_id=""), then=1), default=0, output_field=models.IntegerField())
                    + Case(When(~Q(facebook_key=""), then=1), default=0, output_field=models.IntegerField())
                )
            )
            .order_by("-num_external", "name")
        )
        if keys:
            locations = locations.key_in(keys)
        if types:
            locations = locations.of_type(types)
        if name_contains:
            locations = locations.name_contains(name_contains)
            locations = locations.order_by("-num_external", "-name_match_count", "name")
        if limit:
            limit += offset
        return locations[offset:limit]


class Geolocation(models.Model):
    objects = GeolocationManager.from_queryset(GeolocationQuerySet)()

    key = models.CharField(primary_key=True, max_length=20)
    type = models.CharField(max_length=3, choices=constants.LocationType.get_choices())
    name = models.CharField(max_length=127, blank=False, null=False)
    woeid = models.CharField(max_length=20, blank=True)
    outbrain_id = models.CharField(max_length=40, blank=True)
    facebook_key = models.CharField(max_length=40, blank=True)

    def __str__(self):
        return self.name
