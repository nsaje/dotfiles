from django import forms

from . import model
from . import fields


class CustomFlagsFormMixin(forms.Form):
    custom_flags = fields.CustomFlagsField(
        label='Custom flags',
        required=False,
        widget=forms.widgets.CheckboxSelectMultiple
    )

    def __init__(self, *args, **kwargs):
        self._set_custom_flag_choices()
        super(CustomFlagsFormMixin, self).__init__(*args, **kwargs)

    def _set_custom_flag_choices(self):
        custom_flags_field = self.base_fields['custom_flags']
        if not custom_flags_field:
            return
        custom_flags_field.widget.choices = self._get_current_custom_flags_choices()

    def _get_current_custom_flags_choices(self):
        return model.CustomFlag.objects.all().order_by('name').values_list('id', 'name')
