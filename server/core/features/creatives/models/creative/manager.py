from django.db import transaction

import core.common
import core.models
import dash.constants

from . import exceptions
from . import model


class CreativeManager(core.common.BaseManager):
    @transaction.atomic
    def create(
        self,
        request,
        *,
        agency=None,
        account=None,
        type=dash.constants.AdType.CONTENT,
    ):
        creative = model.Creative(agency=agency, account=account, type=type)
        creative.save(request)
        return creative

    @transaction.atomic
    def bulk_create_from_candidates(self, request, batch, candidates):
        creatives = []
        for candidate in candidates:
            creative = self.create(
                request,
                agency=batch.agency,
                account=batch.account,
                type=candidate["type"],
            )

            creative.update(
                request,
                batch=batch,
                image=self._get_image(candidate),
                icon=self._get_icon(candidate),
                **candidate,
            )

            tags = self._get_tags(batch, candidate)
            creative.set_creative_tags(request, tags)

            creatives.append(creative)
        return creatives

    @staticmethod
    def _get_image(updates):
        if updates.get("type") == dash.constants.AdType.AD_TAG:
            return None
        image_fields = ["image_id", "image_hash", "image_width", "image_height", "image_file_size"]
        if all(updates.get(field) for field in image_fields):
            return core.models.ImageAsset.objects.create(
                image_id=updates["image_id"],
                image_hash=updates["image_hash"],
                width=updates["image_width"],
                height=updates["image_height"],
                file_size=updates["image_file_size"],
                origin_url=updates["image_url"],
            )
        elif any(updates.get(field) for field in image_fields):
            raise exceptions.ImageInvalid("Can not create image due to incomplete data.")
        return None

    @staticmethod
    def _get_icon(updates):
        ad_type = updates.get("type")
        if ad_type == dash.constants.AdType.IMAGE or ad_type == dash.constants.AdType.AD_TAG:
            return None
        icon_fields = ["icon_id", "icon_hash", "icon_height", "icon_width", "icon_file_size"]
        if all(updates.get(field) for field in icon_fields):
            return core.models.ImageAsset.objects.create(
                image_id=updates["icon_id"],
                image_hash=updates["icon_hash"],
                width=updates["icon_width"],
                height=updates["icon_height"],
                file_size=updates["icon_file_size"],
                origin_url=updates["icon_url"],
            )
        elif any(updates.get(field) for field in icon_fields):
            raise exceptions.IconInvalid("Can not create icon due to incomplete data.")
        return None

    @staticmethod
    def _get_tags(batch, updates):
        all_tags = set([tag.name for tag in batch.get_creative_tags()])
        tags = updates.get("tags")
        if tags is not None:
            [all_tags.add(tag) for tag in tags]
        return list(all_tags)
