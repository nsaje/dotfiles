from django.forms.fields import MultiValueField, CharField, IntegerField, FloatField, BooleanField
from .widgets import CustomFlagsWidget


class CustomFlagsField(MultiValueField):
    fields = {"string": CharField, "int": IntegerField, "float": FloatField, "boolean": BooleanField}

    def __init__(self, *args, **kwargs):
        self.entity_flags = kwargs.pop("entity_flags") or {}
        self.all_custom_flags = kwargs.pop("all_custom_flags") or []
        self.widget = CustomFlagsWidget(self.all_custom_flags)
        list_fields = self.get_fields()
        super(CustomFlagsField, self).__init__(list_fields, *args, **kwargs)

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
        return values

    def clean(self, value):
        return self.compress(value)
