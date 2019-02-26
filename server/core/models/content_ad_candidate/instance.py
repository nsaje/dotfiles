import dash.image_helper


class ContentAdCandidateMixin:
    def to_dict(self):
        return {
            "id": self.id,
            "label": self.label,
            "url": self.url,
            "title": self.title,
            "type": self.type,
            "image_url": self.image_url,
            "image_id": self.image_id,
            "image_hash": self.image_hash,
            "image_width": self.image_width,
            "image_height": self.image_height,
            "image_file_size": self.image_file_size,
            "image_crop": self.image_crop,
            "video_asset_id": str(self.video_asset.id) if self.video_asset else None,
            "ad_tag": self.ad_tag,
            "display_url": self.display_url,
            "description": self.description,
            "brand_name": self.brand_name,
            "call_to_action": self.call_to_action,
            "image_status": self.image_status,
            "url_status": self.url_status,
            "hosted_image_url": self.get_image_url(300, 300),
            "landscape_hosted_image_url": self.get_image_url(720, 450),
            "primary_tracker_url": self.primary_tracker_url,
            "secondary_tracker_url": self.secondary_tracker_url,
            "additional_data": self.additional_data,
            "primary_tracker_url_status": self.primary_tracker_url_status,
            "secondary_tracker_url_status": self.secondary_tracker_url_status,
            "can_append_tracking_codes": self.can_append_tracking_codes,
        }

    def get_image_url(self, width=None, height=None):
        if width is None:
            width = self.image_width

        if height is None:
            height = self.image_height

        return dash.image_helper.get_image_url(self.image_id, width, height, self.image_crop)
