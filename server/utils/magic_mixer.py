from mock import Mock
from mixer.backend.django import mixer as mixer_base

from utils import test_helper

import zemauth.models


def get_request_mock(user):
    request = Mock()
    request.user = user
    return request


class MagicMixer(mixer_base.__class__):

    def blend_user(self, permissions=None, is_superuser=False):
        user = self.blend(zemauth.models.User, is_superuser=is_superuser)
        if permissions:
            test_helper.add_permissions(user, permissions)
        return user

    def postprocess(self, target):
        if self.params.get('commit'):
            try:
                target.save()
            except TypeError:
                target.save(request=get_request_mock(self.blend_user()))

        return target


mixer = mixer_base
magic_mixer = MagicMixer()
