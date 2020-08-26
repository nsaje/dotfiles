class PreventUpdatesQuerySetMixin:
    def update(self, *args, **kwargs):
        raise AssertionError("Updating rule history objects is not allowed.")

    def delete(self, *args, **kwargs):
        raise AssertionError("Deleting rule history objects is not allowed.")
