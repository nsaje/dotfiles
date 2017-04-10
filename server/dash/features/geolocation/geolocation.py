# -*- coding: utf-8 -*-

from django.db import models

from dash import constants


class GeolocationQuerySet(models.QuerySet):
    def key_in(self, keys):
        return self.filter(key__in=keys)

    def of_type(self, types):
        return self.filter(type__in=types)

    def name_contains(self, query):
        return self.filter(name__icontains=query)


class GeolocationManager(models.Manager):
    def search(self, keys=None, types=None, name_contains=None, limit=None):
        locations = super(GeolocationManager, self).get_queryset().all()
        if keys:
            locations = locations.key_in(keys)
        if types:
            locations = locations.of_type(types)
        if name_contains:
            locations = locations.name_contains(name_contains)

        return locations[:limit]


class Geolocation(models.Model):
    objects = GeolocationManager.from_queryset(GeolocationQuerySet)()

    class Meta:
        ordering = ('-type',)

    key = models.CharField(
        primary_key=True,
        max_length=20
    )
    type = models.CharField(
        max_length=3,
        choices=constants.LocationType.get_choices()
    )
    name = models.CharField(
        max_length=127,
        blank=False,
        null=False
    )
    woeid = models.CharField(
        max_length=20,
        blank=True,
    )
    outbrain_id = models.CharField(
        max_length=40,
        blank=True,
    )
    facebook_key = models.CharField(
        max_length=40,
        blank=True,
    )

    def __str__(self):
        return self.name
