from django.db import transaction

import core.common
import core.models

from . import model


class CreativeManager(core.common.BaseManager):
    @transaction.atomic
    def create_from_ad(self, request, content_ad):
        """
        Function is used only for product testing.
        TODO (msuber): implement proper mapping.
        """
        creative = model.Creative()

        creative.account = content_ad.ad_group.campaign.account
        creative.type = content_ad.type

        creative.url = content_ad.url
        creative.title = content_ad.title
        creative.display_url = content_ad.display_url
        creative.brand_name = content_ad.brand_name
        creative.description = content_ad.description
        creative.call_to_action = content_ad.call_to_action
        creative.image_crop = content_ad.image_crop

        image_fields = ["image_id", "image_hash", "image_width", "image_height", "image_file_size"]
        if all(getattr(content_ad, field) for field in image_fields):
            creative.image = core.models.ImageAsset.objects.create(
                image_id=content_ad.image_id,
                image_hash=content_ad.image_hash,
                width=content_ad.image_width,
                height=content_ad.image_height,
                file_size=content_ad.image_file_size,
            )

        creative.icon = content_ad.icon
        creative.video_asset = content_ad.video_asset

        creative.ad_tag = content_ad.ad_tag
        creative.trackers = content_ad.trackers
        creative.additional_data = content_ad.additional_data

        creative.save(request)
        return creative
