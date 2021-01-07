class CreativeBatchInstanceMixin(object):
    def save(self, request=None, *args, **kwargs):
        if request and not request.user.is_anonymous:
            if self.pk is None:
                self.created_by = request.user
        super().save(*args, **kwargs)
