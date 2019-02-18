from django.conf import settings
from django.db import transaction

from . import model


class ConversionPixelMixin:
    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)

            if not self.slug:
                # if slug is not provided, id is used as a slug.
                # This is here for backwards compatibility. When
                # none of the pixels with actual string slugs are no
                # longer in use, we can get rid of the slugs altogether
                # and use ids instead.
                model.ConversionPixel.objects.filter(pk=self.id).update(slug=str(self.id))
                self.refresh_from_db()

    def get_url(self):
        return settings.CONVERSION_PIXEL_PREFIX + "{}/{}/".format(self.account.id, self.slug)

    def get_prefix(self):
        return "pixel_{}".format(self.id)

    def get_view_key(self, conversion_window):
        return "{}_{}".format(self.get_prefix(), conversion_window)
