from django.forms.fields import BooleanField
from django.forms.fields import CharField
from django.forms.fields import FloatField
from django.forms.fields import IntegerField
from django.forms.fields import MultiValueField

from .widgets import CustomFlagsWidget


class CustomFlagsField(MultiValueField):
    fields = {"string": CharField, "int": IntegerField, "float": FloatField, "boolean": BooleanField}

    def __init__(self, *args, **kwargs):
        self.entity_flags = kwargs.pop("entity_flags") or {}
        self.all_custom_flags = kwargs.pop("all_custom_flags") or []
        self.widget = CustomFlagsWidget(self.all_custom_flags)
        list_fields = self.get_fields()

        super(CustomFlagsField, self).__init__(list_fields, required=False, require_all_fields=False, *args, **kwargs)

    def get_fields(self):
        fields_type = []
        for cf in self.all_custom_flags:
            if cf.type in CustomFlagsField.fields.keys():
                field_instance = CustomFlagsField.fields[cf.type](
                    required=False, initial=self.entity_flags.get(cf.id, "")
                )
                fields_type.append(field_instance)
        return fields_type

    def compress(self, values):
        if not values:
            return dict()

        mapping = dict(zip([i.id for i in self.all_custom_flags], values))
        for item in self.all_custom_flags:
            if mapping[item.id] is None and item.type == "int":
                mapping[item.id] = int()
            if mapping[item.id] is None and item.type == "float":
                mapping[item.id] = float()
        return mapping
