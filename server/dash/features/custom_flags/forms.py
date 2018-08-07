from django import forms
from . import fields
from . import model


class CustomFlagsFormMixin(forms.Form):
    def __init__(self, data=None, files=None, auto_id="id_%s", prefix=None, initial=None, *args, **kwargs):
        super(CustomFlagsFormMixin, self).__init__(data, files, auto_id, prefix, initial, *args, **kwargs)
        self.fields["custom_flags"] = fields.CustomFlagsField(
            entity_flags=initial.get("custom_flags", {}),
            all_custom_flags=list(model.CustomFlag.objects.all().order_by("advanced")),
            help_text="Fields with a background color are advanced flags.",
        )

    def clean_custom_flags(self):
        entity_flags = self.instance.custom_flags or dict()
        updated_flags = entity_flags.items() - self.cleaned_data.get("custom_flags").items()
        advanced_updated_flags = (
            model.CustomFlag.objects.filter(id__in=[i[0] for i in updated_flags])
            .filter(advanced=True)
            .all()
            .values_list("name", flat=True)
        )

        if advanced_updated_flags and not self.request.user.has_perm("zemauth.can_edit_advanced_custom_flags"):
            msg = "Advanced Flags ({}) can only be modified by admin.".format(", ".join([*advanced_updated_flags]))
            raise forms.ValidationError(msg)
        return self.cleaned_data.get("custom_flags")
