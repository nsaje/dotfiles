from django.db.models import OneToOneField
from django.db.models.fields.related_descriptors import ForwardOneToOneDescriptor


class CachedForwardOneToOneDescriptor(ForwardOneToOneDescriptor):
    def get_object(self, instance):
        model_to_field = {
            "adgroupsource": "ad_group_source",
            "adgroup": "ad_group",
            "campaign": "campaign",
            "account": "account",
            "agency": "agency",
        }
        # Get related object for this instance.
        obj = super().get_object(instance)

        # Resolve field name for reverse reference to this instance.
        model_name = self.field.model._meta.model_name
        field_name = model_to_field[model_name]

        # Manually prepopulate field cache with reverse reference to this instance.
        obj._state.fields_cache[field_name] = instance
        return obj


class CachedOneToOneField(OneToOneField):
    """
    OneToOneField that caches reverse reference on related field.

    This field is designed to work with core.models.settings.settings_base.SettingsBase models.
    """

    forward_related_accessor_class = CachedForwardOneToOneDescriptor
