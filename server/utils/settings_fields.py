import logging

from django.db.models import OneToOneField
from django.db.models.fields.related_descriptors import ForwardOneToOneDescriptor


logger = logging.getLogger(__name__)


def resolve_related_model_field_name(settings_instance):
    """
    Resolve related model field name for input core.models.settings.settings_base.SettingsBase instance.

    :param settings_instance: a core.models.settings.settings_base.SettingsBase instance
    :return: the name of related model field or None if it could not be resolved
    """

    model_to_field = {
        "adgroupsource": "ad_group_source",
        "adgroup": "ad_group",
        "campaign": "campaign",
        "account": "account",
        "agency": "agency",
    }

    # Resolve field name for reverse reference to this instance.
    model_name = settings_instance._meta.get_field("latest_for_entity").related_model._meta.model_name
    if model_name in model_to_field:
        return model_to_field[model_name]

    else:
        logger.error("Unsupported related model: %s", model_name)
        return None


class CachedForwardOneToOneDescriptor(ForwardOneToOneDescriptor):
    """ForwardOneToOneDescriptor that caches reverse reference."""

    def __get__(self, instance, cls=None):
        rel_obj = super().__get__(instance, cls=cls)

        if rel_obj is not None:
            field_name = resolve_related_model_field_name(rel_obj)

            if field_name is not None:
                # Manually prepopulate field cache with reverse reference to this instance.
                rel_obj._state.fields_cache[field_name] = instance

        return rel_obj


class CachedOneToOneField(OneToOneField):
    """
    OneToOneField that caches reverse reference on related field.

    This field is designed to work with core.models.settings.settings_base.SettingsBase models.
    """

    forward_related_accessor_class = CachedForwardOneToOneDescriptor
