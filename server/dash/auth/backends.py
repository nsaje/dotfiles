from django.forms import ValidationError
from django.contrib.auth import models, backends
from django.core.validators import validate_email

class EmailOrUsernameModelBackend(backends.ModelBackend):
    def authenticate(self, username=None, password=None):
        try:
            validate_email(username)
            kwargs = {'email': username}
        except ValidationError:
            kwargs = {'username': username}

        try:
            user = models.User.objects.get(**kwargs)
            if user.check_password(password):
                return user

            return None                
        except models.User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return models.User.objects.get(pk=user_id)
        except models.User.DoesNotExist:
            return None
