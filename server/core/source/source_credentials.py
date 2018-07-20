# -*- coding: utf-8 -*-
import binascii

from django.conf import settings
from django.db import models

from utils import encryption_helpers


class SourceCredentials(models.Model):
    class Meta:
        app_label = "dash"
        verbose_name_plural = "Source Credentials"

    id = models.AutoField(primary_key=True)
    source = models.ForeignKey("Source", on_delete=models.PROTECT)
    name = models.CharField(max_length=127, editable=True, blank=False, null=False)
    credentials = models.TextField(blank=True, null=False)
    sync_reports = models.BooleanField(default=True)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        try:
            existing_instance = SourceCredentials.objects.get(id=self.id)
        except SourceCredentials.DoesNotExist:
            existing_instance = None

        if (not existing_instance) or (existing_instance and existing_instance.credentials != self.credentials):
            encrypted_credentials = encryption_helpers.aes_encrypt(
                self.credentials, settings.CREDENTIALS_ENCRYPTION_KEY
            )
            self.credentials = binascii.b2a_base64(encrypted_credentials)

        super(SourceCredentials, self).save(*args, **kwargs)

    def decrypt(self):
        if not self.id or not self.credentials:
            return self.credentials

        return encryption_helpers.aes_decrypt(
            binascii.a2b_base64(self.credentials), settings.CREDENTIALS_ENCRYPTION_KEY
        )
