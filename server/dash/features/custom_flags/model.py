from django.db import models


class CustomFlag(models.Model):
    id = models.CharField(primary_key=True, max_length=255)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
