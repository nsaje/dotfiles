import operator

from django.contrib.auth import models as auth_models
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.core import validators
from django.core.exceptions import ValidationError


class UserManager(auth_models.BaseUserManager):
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

    def get_users_with_perm(self, perm_name, include_superusers=False):
        perm = auth_models.Permission.objects.get(codename=perm_name)

        query_list = [
            models.Q(groups__permissions=perm),
            models.Q(user_permissions=perm)
        ]

        if include_superusers:
            query_list.append(models.Q(is_superuser=True))

        return self.filter(reduce(operator.or_, query_list)).distinct()


class User(auth_models.AbstractBaseUser, auth_models.PermissionsMixin):
    ''' Describes custom Zemanta user.

    IMPORTANT: Default unique constraint on the email created by Django is deleted and
    replaced by case-insensitive unique index created by one of migrations.
    '''
    email = models.EmailField(_('email address'), max_length=255, unique=True)
    username = models.CharField(
        _('username'),
        max_length=30,
        blank=True,
        help_text=_('30 characters or fewer. Letters, digits and '
                    '@/./+/-/_ only.'),
        validators=[
            validators.RegexValidator(r'^[\w.@+-]+$', _('Enter a valid username.'), 'invalid')
        ]
    )
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin '
                    'site.')
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Designates whether this user should be treated as '
                    'active. Unselect this instead of deleting accounts.')
    )

    show_onboarding_guidance = models.BooleanField(
        default=False,
        help_text='Designates weather user has self-manage access and needs onboarding guidance.'
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

        permissions = (
            ('campaign_settings_view', "Can view campaign's settings tab."),
            ('campaign_agency_view', "Can view campaign's agency tab."),
            ('campaign_ad_groups_view', "Can view campaign's ad groups tab in dashboard."),
            ('campaign_settings_account_manager', 'Can be chosen as account manager.'),
            ('campaign_settings_sales_rep', 'Can be chosen as sales representative.'),
            ('help_view', 'Can view help popovers.'),
            ("supply_dash_link_view", "Can view supply dash link."),
            ('ad_group_agency_tab_view', "Can view ad group's agency tab."),
            ('all_accounts_accounts_view', "Can view all accounts's accounts tab."),
            ('account_campaigns_view', "Can view accounts's campaigns tab."),
            ('account_agency_view', "Can view accounts's agency tab."),
            ('ad_group_sources_add_source', "Can add media sources."),
            ('campaign_sources_view', 'Can view campaign sources view.'),
            ('account_sources_view', 'Can view account sources view.'),
            ('all_accounts_sources_view', 'Can view all accounts sources view.'),
            ('campaign_ad_groups_add_ad_group', 'Can add ad groups.'),
            ('account_campaigns_add_campaign', 'Can add campaigns.'),
            ('all_accounts_accounts_add_account', 'Can add accounts.'),
            ('all_new_sidebar', 'Can see new sidebar.'),
            ('campaign_budget_management_view', 'Can do campaign budget management.'),
            ('account_budget_view', 'Can view account budget.'),
            ('all_accounts_budget_view', 'Can view all accounts budget.'),
            ('archive_restore_entity', 'Can archive or restore an entity.'),
            ('view_archived_entities', 'Can view archived entities.'),
            ('unspent_budget_view', 'Can view unspent budget.'),
            ('switch_to_demo_mode', 'Can switch to demo mode.'),
            ('account_agency_access_permissions', 'Can view and set account access permissions.'),
            ('group_new_user_add', 'New users are added to this group.'),
            ('set_ad_group_source_settings', 'Can set per-source settings.'),
            ('see_current_ad_group_source_state', 'Can see current per-source state.'),
            ('campaign_ad_groups_detailed_report', 'Can download detailed report on campaign level.'),
            ('content_ads_postclick_acquisition', 'Can view content ads postclick acq. metrics.'),
            ('content_ads_postclick_engagement', 'Can view content ads postclick eng. metrics.'),
            ('aggregate_postclick_acquisition', 'Can view aggregate postclick acq. metrics.'),
            ('aggregate_postclick_engagement', 'Can view aggregate postclick eng. metrics.'),
            ('data_status_column', 'Can see data status column in table.'),
            ('new_content_ads_tab', 'Can view new content ads tab.'),
            ('filter_sources', 'Can filter sources'),
            ('upload_content_ads', 'Can upload new content ads.'),
            ('set_content_ad_status', 'Can set status of content ads.'),
            ('get_content_ad_csv', 'Can download bulk content ad csv.'),
            ('content_ads_bulk_actions', 'Can view and use bulk content ads actions.'),
            ('can_toggle_ga_performance_tracking', 'Can toggle Google Analytics performance tracking.'),
            ('can_toggle_adobe_performance_tracking', 'Can toggle Adobe Analytics performance tracking.'),
            ('can_see_media_source_status_on_submission_popover', 'Can see media source status on submission status popover'),
            ('can_set_dma_targeting', 'Can set DMA targeting'),
            ('can_set_media_source_to_auto_pilot', 'Can set media source to auto-pilot'),
            ('manage_conversion_pixels', 'Can manage conversion pixels'),
            ('has_intercom', 'Can see intercom widget'),
        )

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

    def clean(self):
        if not self.pk and self.__class__.objects.filter(email=self.email.lower).exists():
            raise ValidationError({'email': 'User with this e-mail already exists.'})

    def get_all_permissions_with_access_levels(self):
        if not self.is_active or self.is_anonymous():
            return {}

        perm_cache_name = '_zemauth_permission_cache'
        if not hasattr(self, perm_cache_name):
            if self.is_superuser:
                perms = auth_models.Permission.objects.all()
            else:
                perms = auth_models.Permission.objects.\
                    filter(models.Q(user=self) | models.Q(group__user=self)).\
                    order_by('id').\
                    distinct('id')

            public_permissions = auth_models.Permission.objects.\
                filter(pk__in=(x.pk for x in perms)).\
                filter(group__in=auth_models.Group.objects.filter(internalgroup=None))

            public_permissions_ids = [x.pk for x in public_permissions]

            permissions = {'{}.{}'.format(x.content_type.app_label, x.codename): x.pk in public_permissions_ids for x in perms}

            setattr(self, perm_cache_name, permissions)

        return getattr(self, perm_cache_name)


class InternalGroup(models.Model):
    group = models.OneToOneField(auth_models.Group, on_delete=models.PROTECT)

    def __unicode__(self):
        return self.group.name
