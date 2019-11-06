class RuleHistoryInstanceMixin:
    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise AssertionError("Updating rule history object is not allowed.")

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise AssertionError("Deleting rule history object is not allowed.")
