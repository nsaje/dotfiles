from django import forms

from . import exceptions
from . import models


class SubmissionFilterForm(forms.ModelForm):
    def clean(self):
        obj = models.SubmissionFilter(**self.cleaned_data)
        check_existing = False if set(self.changed_data.keys()) == {"description"} else True

        possible_keys = [obj.agency_id, obj.account_id, obj.campaign_id, obj.ad_group_id, obj.content_ad_id]
        if len([key for key in possible_keys if key is not None]) != 1:
            raise exceptions.MultipleFilterEntitiesException("Multiple level entities not allowed.")

        _, level, level_id = obj.get_lookup_key()
        models.SubmissionFilterManager.validate(
            obj.source, obj.state, {level + "_id": level_id}, check_existing=check_existing
        )

        return self.cleaned_data

    class Meta:
        model = models.SubmissionFilter
        exclude = tuple()
