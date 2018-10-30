# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import models

import core.models
import utils.exc
from dash import constants
from utils import dates_helper


class UploadBatchManager(models.Manager):
    def create(self, user, account, name, ad_group=None):
        if ad_group is not None:
            core.common.entity_limits.enforce(
                core.models.ContentAd.objects.filter(ad_group=ad_group).exclude_archived(), account.id
            )
        batch = UploadBatch(account=account, name=name, ad_group=ad_group)
        batch.save(user=user)
        return batch

    def clone(self, user, source_ad_group, ad_group, new_batch_name=None):
        account = ad_group.campaign.account
        return self.create(user, account, new_batch_name or UploadBatch.generate_cloned_name(source_ad_group), ad_group)

    def create_for_file(self, user, account, name, ad_group, original_filename, auto_save, is_edit):
        core.common.entity_limits.enforce(
            core.models.ContentAd.objects.filter(ad_group=ad_group).exclude_archived(), account.id
        )
        batch = UploadBatch(
            account=account, name=name, ad_group=ad_group, original_filename=original_filename, auto_save=auto_save
        )

        if is_edit:
            batch.type = constants.UploadBatchType.EDIT

        batch.save(user=user)
        return batch


class UploadBatch(models.Model):
    class Meta:
        app_label = "dash"
        get_latest_by = "created_dt"

    _demo_fields = {"name": lambda: "upload.csv"}

    name = models.CharField(max_length=1024)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="+", on_delete=models.PROTECT, null=True, blank=True
    )
    status = models.IntegerField(
        default=constants.UploadBatchStatus.IN_PROGRESS, choices=constants.UploadBatchStatus.get_choices()
    )
    type = models.IntegerField(
        default=constants.UploadBatchType.INSERT, choices=constants.UploadBatchType.get_choices()
    )
    account = models.ForeignKey("Account", on_delete=models.PROTECT, null=True)
    ad_group = models.ForeignKey("AdGroup", on_delete=models.PROTECT, null=True, blank=True)
    original_filename = models.CharField(max_length=1024, null=True)

    default_image_crop = models.TextField(null=True, blank=True, default=constants.ImageCrop.CENTER)
    default_display_url = models.TextField(null=True, blank=True, default="")
    default_brand_name = models.TextField(null=True, blank=True, default="")
    default_description = models.TextField(null=True, blank=True, default="")
    default_call_to_action = models.TextField(null=True, blank=True, default=constants.DEFAULT_CALL_TO_ACTION)

    auto_save = models.BooleanField(default=False)

    objects = UploadBatchManager()

    def get_approved_content_ads(self):
        return self.contentad_set.all().order_by("pk")

    def save(self, *args, **kwargs):
        if self.pk is None:
            user = kwargs.pop("user", None)
            self.created_by = user
        super(UploadBatch, self).save(*args, **kwargs)

    @classmethod
    def generate_cloned_name(cls, source_ad_group):
        return "Cloned from {} on {}".format(
            source_ad_group.get_name_with_id(), dates_helper.format_date_mmddyyyy(dates_helper.local_now())
        )

    def mark_save_done(self):
        self.status = constants.UploadBatchStatus.DONE
        self.save()

    def set_ad_group(self, ad_group):
        if self.status == constants.UploadBatchStatus.DONE:
            raise utils.exc.ForbiddenError("Cannot set an ad group on an already persisted batch")
        self.ad_group = ad_group
        candidates = core.models.ContentAdCandidate.objects.filter(batch=self)
        candidates.update(ad_group=ad_group)
        self.save()
