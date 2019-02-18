import binascii

from django.conf import settings

from utils import encryption_helpers


class SourceCredentialsMixin:
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        try:
            # Todo: Fix circular depency
            from .model import SourceCredentials

            existing_instance = SourceCredentials.objects.get(id=self.id)
        except SourceCredentials.DoesNotExist:
            existing_instance = None

        if (not existing_instance) or (existing_instance and existing_instance.credentials != self.credentials):
            encrypted_credentials = encryption_helpers.aes_encrypt(
                self.credentials, settings.CREDENTIALS_ENCRYPTION_KEY
            )
            self.credentials = binascii.b2a_base64(encrypted_credentials)

        super().save(*args, **kwargs)

    def decrypt(self):
        if not self.id or not self.credentials:
            return self.credentials

        return encryption_helpers.aes_decrypt(
            binascii.a2b_base64(self.credentials), settings.CREDENTIALS_ENCRYPTION_KEY
        )
