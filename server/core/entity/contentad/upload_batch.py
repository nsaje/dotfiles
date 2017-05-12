# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import models

from dash import constants


class UploadBatchManager(models.Manager):

    def create(self, user, name, ad_group_id):
        batch = UploadBatch(
            name=name,
            ad_group_id=ad_group_id,
        )
        batch.save(user=user)
        return batch

    def create_for_file(self, user, name, ad_group_id, original_filename, auto_save, is_edit):
        batch = UploadBatch(
            name=name,
            ad_group_id=ad_group_id,
            original_filename=original_filename,
            auto_save=auto_save,
        )

        if is_edit:
            batch.type = constants.UploadBatchType.EDIT

        batch.save(user=user)
        return batch


class UploadBatch(models.Model):
    class Meta:
        app_label = 'dash'
        get_latest_by = 'created_dt'

    _demo_fields = {'name': lambda: 'upload.csv'}

    name = models.CharField(max_length=1024)
    created_dt = models.DateTimeField(
        auto_now_add=True, verbose_name='Created at')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='+',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    status = models.IntegerField(
        default=constants.UploadBatchStatus.IN_PROGRESS,
        choices=constants.UploadBatchStatus.get_choices()
    )
    type = models.IntegerField(
        default=constants.UploadBatchType.INSERT,
        choices=constants.UploadBatchType.get_choices()
    )
    ad_group = models.ForeignKey('AdGroup', on_delete=models.PROTECT, null=True)
    original_filename = models.CharField(max_length=1024, null=True)

    default_image_crop = models.TextField(
        null=True, blank=True, default=constants.ImageCrop.CENTER)
    default_display_url = models.TextField(null=True, blank=True, default="")
    default_brand_name = models.TextField(null=True, blank=True, default="")
    default_description = models.TextField(null=True, blank=True, default="")
    default_call_to_action = models.TextField(
        null=True, blank=True, default=constants.DEFAULT_CALL_TO_ACTION)

    auto_save = models.BooleanField(default=False)

    objects = UploadBatchManager()

    def get_approved_content_ads(self):
        return self.contentad_set.all().order_by('pk')

    def save(self, *args, **kwargs):
        if self.pk is None:
            user = kwargs.pop('user', None)
            self.created_by = user
        super(UploadBatch, self).save(*args, **kwargs)
