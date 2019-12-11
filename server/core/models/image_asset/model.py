from django.db import models

import dash.constants

from . import manager


class ImageAsset(models.Model):
    class Meta:
        app_label = "dash"

    objects = manager.ImageAssetManager()

    image_id = models.CharField(primary_key=True, max_length=256, editable=False)
    image_hash = models.CharField(max_length=128)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    file_size = models.PositiveIntegerField()
    origin_url = models.URLField(null=True, blank=True)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")

    def get_base_url(self):
        if self.image_id is None:
            return None

        return dash.image_helper.get_base_image_url(self.image_id)

    def get_url(self, width=None, height=None, crop=None):
        if self.image_id is None:
            return None

        if width is None:
            width = self.width

        if height is None:
            height = self.height

        if crop is None:
            crop = dash.constants.ImageCrop.CENTER

        return dash.image_helper.get_image_url(self.image_id, width, height, crop)
