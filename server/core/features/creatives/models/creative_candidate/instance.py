from django.db import transaction

import dash.constants
from dash import image_helper


class CreativeCandidateInstanceMixin(object):
    def save(self, request=None, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @transaction.atomic
    def update(self, request, **updates):
        self._handle_image(updates)
        self._handle_icon(updates)

        cleaned_updates = self._clean_updates(updates)
        if not cleaned_updates:
            return

        self._apply_updates(cleaned_updates)
        self.save(request)

    def delete(self, using=None, keep_parents=False):
        if self.batch.status != dash.constants.CreativeBatchStatus.IN_PROGRESS:
            raise AssertionError("Batch status is not in progress")
        super(CreativeCandidateInstanceMixin, self).delete()

    def _clean_updates(self, updates):
        new_updates = {}
        for field, value in list(updates.items()):
            if field in set(self._update_fields) and value != getattr(self, field):
                new_updates[field] = value
        return new_updates

    def _apply_updates(self, updates):
        for field, value in list(updates.items()):
            setattr(self, field, value)

    def _handle_image(self, updates):
        image = updates.get("image")
        if image is None:
            return
        image_url = image_helper.upload_image_to_s3(image, self.batch_id)
        updates["image_url"] = image_url

    def _handle_icon(self, updates):
        icon = updates.get("icon")
        if icon is None:
            return
        icon_url = image_helper.upload_image_to_s3(icon, self.batch_id)
        updates["icon_url"] = icon_url

    @property
    def hosted_image_url(self):
        return self.get_image_url(300, 300)

    @property
    def landscape_hosted_image_url(self):
        return self.get_image_url(720, 450)

    @property
    def portrait_hosted_image_url(self):
        return self.get_image_url(375, 480)

    @property
    def display_hosted_image_url(self):
        return self.get_image_url()

    @property
    def hosted_icon_url(self):
        return self.get_icon_url(300)

    def get_image_url(self, width=None, height=None):
        if not self.image:
            return None
        if width is None:
            width = self.image.width
        if height is None:
            height = self.image.height
        return self.image.get_url(width=width, height=height, crop=self.image_crop)

    def get_icon_url(self, size=None):
        if not self.icon:
            return None
        if size is None:
            size = self.icon.width
        return self.icon.get_url(width=size, height=size)
