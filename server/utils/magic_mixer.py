from mock import Mock
from mixer.backend.django import mixer as mixer_base
from django.contrib.postgres.fields import ArrayField

from utils import test_helper

import zemauth.models
import core.entity
import core.source


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

        source = self.blend(core.source.Source, **{k: v for k, v in list(kwargs.items()) if not k.startswith(kw)})
        self.blend(core.source.DefaultSourceSettings, source=source, credentials=self.RANDOM, **dss_kwargs)
        return source

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
