from django.db import transaction


class CreativeInstanceMixin(object):
    def save(self, request=None, *args, **kwargs):
        if request and not request.user.is_anonymous:
            if self.pk is None:
                self.created_by = request.user
            else:
                self.modified_by = request.user
        super().save(*args, **kwargs)

    @transaction.atomic
    def update(self, request, **updates):
        self.clean(updates)

        cleaned_updates = self._clean_updates(updates)
        if not updates:
            return

        self._apply_updates(request, cleaned_updates)
        self.save(request)

    def _clean_updates(self, updates):
        new_updates = {}
        for field, value in list(updates.items()):
            if field in set(self._update_fields) and value != getattr(self, field):
                new_updates[field] = value
        return new_updates

    def _apply_updates(self, updates):
        for field, value in list(updates.items()):
            setattr(self, field, value)

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
