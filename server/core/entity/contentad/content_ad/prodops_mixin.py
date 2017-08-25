

class ProdopsMixin(object):

    def get_prodops_dict(self):
        return {
            'id': self.pk,
            'ad_group__name': self.ad_group.name,
            'ad_group__id': self.ad_group.id,
            'ad_group__campaign_id__name': self.ad_group.campaign.name,
            'ad_group__campaign_id__id': self.ad_group.campaign.id,
            'label': self.label,
            'url': self.url,
            'title': self.title,
            'display_url': self.display_url,
            'brand_name': self.brand_name,
            'description': self.description,
            'call_to_action': self.call_to_action,
            'image_url': self.get_image_url(),
            'image_id': self.image_id,
            'image_hash': self.image_hash,
            'image_width': self.image_width,
            'image_height': self.image_height,
            'image_crop': self.image_crop,
            'video_asset_id': str(self.video_asset.id) if self.video_asset else None,
            'primary_tracker_url': self.tracker_urls[0] if self.tracker_urls else None,
            'secondary_tracker_url': self.tracker_urls[1] if self.tracker_urls and len(self.tracker_urls) > 1 else None,
        }
