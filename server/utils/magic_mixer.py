from mock import Mock
from mixer.backend.django import mixer as mixer_base
from django.contrib.postgres.fields import ArrayField

from utils import test_helper

import zemauth.models


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

    def postprocess(self, target):
        if self.params.get('commit'):
            try:
                target.save()
            except TypeError:
                target.save(request=get_request_mock(self.blend_user()))

        return target


mixer = mixer_base
magic_mixer = MagicMixer()
