class DefaultSourceSettingsMixin:
    def __str__(self):
        return self.source.name
