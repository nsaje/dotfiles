from django.db import models

import dash.constants


class Geolocation(models.Model):

    class Meta:
        ordering = ('-type',)

    key = models.CharField(
        primary_key=True,
        max_length=20
    )
    type = models.CharField(
        max_length=3,
        choices=dash.constants.LocationType.get_choices()
    )
    name = models.CharField(
        max_length=127,
        blank=False,
        null=False
    )

    def __str__(self):
        return self.name
