import logging

from django.db.models import OneToOneField
from django.db.models.fields.related_descriptors import ForwardOneToOneDescriptor


logger = logging.getLogger(__name__)


class CachedForwardOneToOneDescriptor(ForwardOneToOneDescriptor):
    def __get__(self, instance, cls=None):
        rel_obj = super().__get__(instance, cls=cls)

        model_to_field = {
            "adgroupsource": "ad_group_source",
            "adgroup": "ad_group",
            "campaign": "campaign",
            "account": "account",
            "agency": "agency",
        }

        # Resolve field name for reverse reference to this instance.
        model_name = rel_obj._meta.get_field("latest_for_entity").related_model._meta.model_name
        if model_name in model_to_field:
            field_name = model_to_field[model_name]

            # Manually prepopulate field cache with reverse reference to this instance.
            rel_obj._state.fields_cache[field_name] = instance
        else:
            logger.error("Unsupported related model: %s", model_name)

        return rel_obj


class CachedOneToOneField(OneToOneField):
    """
    OneToOneField that caches reverse reference on related field.

    This field is designed to work with core.models.settings.settings_base.SettingsBase models.
    """

    forward_related_accessor_class = CachedForwardOneToOneDescriptor
