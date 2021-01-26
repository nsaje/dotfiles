import datetime

from django.contrib.postgres.fields import ArrayField
from mixer.backend.django import mixer as mixer_base
from mock import Mock

import core.models
import dash.constants
import zemauth.models
from utils import dates_helper
from utils import test_helper


def get_request_mock(user):
    request = Mock()
    request.user = user
    return request


class MagicMixer(mixer_base.__class__):
    def blend(self, model, **kwargs):
        for field in model._meta.fields:
            if isinstance(field, ArrayField) and field.name not in kwargs:
                # TODO a hack over mixer that doesn't know how to handler ArrayField
                kwargs[field.name] = []

        return super(MagicMixer, self).blend(model, **kwargs)

    def blend_user(self, permissions=None, is_superuser=False):
        user = self.blend(zemauth.models.User, is_superuser=is_superuser)
        if permissions:
            test_helper.add_permissions(user, permissions)
        return user

    def blend_request_user(self, permissions=None, is_superuser=False):
        # shortcut
        return get_request_mock(self.blend_user(permissions, is_superuser))

    def blend_source_w_defaults(self, **kwargs):
        kw = "default_source_settings"
        dss_kwargs = {k[25:]: v for k, v in list(kwargs.items()) if k.startswith(kw)}

        source = self.blend(core.models.Source, **{k: v for k, v in list(kwargs.items()) if not k.startswith(kw)})
        self.blend(core.models.DefaultSourceSettings, source=source, credentials=self.RANDOM, **dss_kwargs)
        return source

    def blend_budget_line_item(self, **kwargs):
        start_date = kwargs.pop("start_date", dates_helper.local_today())
        end_date = kwargs.pop("end_date", dates_helper.local_today() + datetime.timedelta(days=3))
        amount = kwargs.pop("amount", 500.0)
        credit = kwargs.pop("credit", None)
        if not credit:
            campaign = kwargs.pop("campaign", None)
            account = campaign.account if campaign else kwargs.pop("account", None)
            if not account:
                account = self.blend(core.models.Account)
            credit = self.blend(
                core.features.bcm.CreditLineItem,
                start_date=start_date - datetime.timedelta(days=5),
                end_date=end_date + datetime.timedelta(days=5),
                amount=amount + 100.0,
                status=dash.constants.CreditLineItemStatus.SIGNED,
                account=account,
            )
        return self.blend(
            core.features.bcm.BudgetLineItem,
            credit=credit,
            start_date=start_date,
            end_date=end_date,
            amount=amount,
            campaign=campaign,
            **kwargs,
        )

    def postprocess(self, target):
        if self.params.get("commit"):

            def _save():
                try:
                    target.save()
                except TypeError:
                    target.save(request=get_request_mock(self.blend_user()))

            _save()

            for field in target._meta.fields:
                if field.name == "settings":
                    back_field_name = None
                    for settings_field in field.remote_field.model._meta.get_fields():
                        if (
                            settings_field.remote_field is not None
                            and hasattr(settings_field, "attname")
                            and settings_field.remote_field.model == target.__class__
                        ):
                            back_field_name = settings_field.name
                    params = {back_field_name: target}
                    params.update(**field.remote_field.model.get_defaults_dict())
                    settings = field.remote_field.model(**params)
                    settings.update_unsafe(None)
                    target.settings = settings
                    _save()

        return target


mixer = mixer_base
magic_mixer = MagicMixer()
