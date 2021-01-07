class CreativeTagMixin(object):
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
