import datetime
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

    def blend_latest_settings(self, parent, **kwargs):
        latest_settings = parent.get_current_settings()
        kwargs[parent.settings.field.name] = parent
        return self.blend(parent.settings.model,
                          created_dt=latest_settings.created_dt + datetime.timedelta(days=1),
                          **kwargs)

    def blend_source_w_defaults(self, **kwargs):
        kw = 'default_source_settings'
        dss_kwargs = {k[25:]: v for k, v in kwargs.items() if k.startswith(kw)}

        source = self.blend(core.source.Source, **{k: v for k, v in kwargs.items() if not k.startswith(kw)})
        self.blend(core.source.DefaultSourceSettings,
                   source=source, credentials=self.RANDOM, **dss_kwargs)
        return source

    def postprocess(self, target):
        if self.params.get('commit'):
            try:
                target.save()
            except TypeError:
                target.save(request=get_request_mock(self.blend_user()))

        return target


mixer = mixer_base
magic_mixer = MagicMixer()
