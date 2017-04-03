# -*- coding: utf-8 -*-

from django.db import models

from dash import constants


class GeolocationManager(models.Manager):
    def map(self, keys):
        return super(GeolocationManager, self).get_queryset().filter(key__in=keys)

    def search(self, query):
        return super(GeolocationManager, self).get_queryset().filter(name__icontains=query)


class Geolocation(models.Model):
    objects = GeolocationManager()

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

    def __str__(self):
        return self.name
