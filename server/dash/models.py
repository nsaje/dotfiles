from django.contrib.auth import models as auth_models
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.core import validators
import jsonfield

import constants

class CustomUserManager(auth_models.BaseUserManager):
    def _create_user(self, email, password, is_staff, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        now = timezone.now()
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email,
                          is_staff=is_staff, is_active=True,
                          is_superuser=is_superuser, last_login=now,
                          date_joined=now, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        return self._create_user(email, password, False, False, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        return self._create_user(email, password, True, True, **extra_fields)

class CustomUser(auth_models.AbstractBaseUser, auth_models.PermissionsMixin):
    email = models.EmailField(_('email address'), max_length=255, unique=True)
    username = models.CharField(_('username'), max_length=30, blank=True,
        help_text=_('30 characters or fewer. Letters, digits and '
                    '@/./+/-/_ only.'),
        validators=[
            validators.RegexValidator(r'^[\w.@+-]+$', _('Enter a valid username.'), 'invalid')
        ])
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    is_staff = models.BooleanField(_('staff status'), default=False,
        help_text=_('Designates whether the user can log into this admin '
                    'site.'))
    is_active = models.BooleanField(_('active'), default=True,
        help_text=_('Designates whether this user should be treated as '
                    'active. Unselect this instead of deleting accounts.'))

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        "Returns the short name for the user."
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)
        
    def __unicode__(self):
        return self.email

class Account(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=127,
        editable=True,
        unique=True,
        blank=False,
        null=False
    )
    users = models.ManyToManyField(settings.AUTH_USER_MODEL)
    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)


class Campaign(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=127,
        editable=True,
        blank=False,
        null=False
    )
    account = models.ForeignKey(Account)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL)
    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)


class AdGroup(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=127,
        editable=True,
        blank=False,
        null=False
    )
    campaign = models.ForeignKey(Campaign)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL)
    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)


class Network(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=127,
        editable=True,
        blank=False,
        null=False
    )
    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)


class AdGroupSettings(models.Model):
    id = models.AutoField(primary_key=True)
    ad_group = models.ForeignKey(AdGroup)
    created_datetime = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(
        default=constants.AdGroupSettingsStatus.INACTIVE,
        choices=constants.AdGroupSettingsStatus.get_choices()
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    cpc_cc = models.DecimalField(default=0, max_digits=10, decimal_places=4)
    budget_day_cc = models.DecimalField(default=0, max_digits=10, decimal_places=4)
    target_devices = jsonfield.JSONField(blank=True)
    target_regions = jsonfield.JSONField(blank=True)
    tracking_code = models.TextField(blank=True)


class AdGroupNetworkSettings(models.Model):
    id = models.AutoField(primary_key=True)
    network = models.ForeignKey(Network)
    ad_group = models.ForeignKey(AdGroup)
    created_datetime = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(
        default=constants.AdGroupNetworkSettingsStatus.INACTIVE,
        choices=constants.AdGroupNetworkSettingsStatus.get_choices()
    )
    cpc_cc = models.DecimalField(default=0, max_digits=10, decimal_places=4)
    budget_day_cc = models.DecimalField(default=0, max_digits=10, decimal_places=4)
