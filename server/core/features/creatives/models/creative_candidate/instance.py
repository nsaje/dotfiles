from django.db import transaction

import core.features.creatives.models.creative_batch.exceptions
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
            raise core.features.creatives.models.creative_batch.exceptions.BatchStatusInvalid()
        super(CreativeCandidateInstanceMixin, self).delete()

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

    def to_dict(self):
        return {
            "id": self.id,
            "batch_id": self.batch.id if self.batch is not None else None,
            "type": dash.constants.AdType.get_name(self.type) if self.type is not None else None,
            "url": self.url,
            "title": self.title,
            "display_url": self.display_url,
            "brand_name": self.brand_name,
            "description": self.description,
            "call_to_action": self.call_to_action,
            "image_crop": self.image_crop,
            "image_id": self.image_id,
            "image_hash": self.image_hash,
            "image_width": self.image_width,
            "image_height": self.image_height,
            "image_file_size": self.image_file_size,
            "image_url": self.image_url,
            "icon_id": self.icon_id,
            "icon_hash": self.icon_hash,
            "icon_width": self.icon_width,
            "icon_height": self.icon_height,
            "icon_file_size": self.icon_file_size,
            "icon_url": self.icon_url,
            "video_asset_id": self.video_asset.id if self.video_asset is not None else None,
            "ad_tag": self.ad_tag,
            "tags": [tag.name for tag in self.get_creative_tags()],
            "trackers": self.trackers,
            "additional_data": self.additional_data,
        }

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
