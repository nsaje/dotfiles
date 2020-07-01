import mock
from django.contrib.auth.models import ContentType
from django.contrib.auth.models import Permission
from django.test import TestCase
from rest_framework import pagination

import core.models
from utils.magic_mixer import magic_mixer

from . import constants
from . import helpers
from . import model


class LogDifferencesPaginator(pagination.BasePagination):
    def __init__(self, offset, limit):
        self.offset = offset
        self.limit = limit

    def paginate_queryset(self, queryset, request, view=None):
        return list(queryset[self.offset : self.offset + self.limit])


class HelpersTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.content_type = magic_mixer.blend(ContentType, app_label="zemauth")
        cls.permission = magic_mixer.blend(
            Permission, codename="fea_use_entity_permission", content_type=cls.content_type
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.permission.delete()
        cls.content_type.delete()

    @mock.patch("zemauth.features.entity_permission.helpers.logger")
    def test_query_all_for_agency_manager(self, mock_logger):
        user = magic_mixer.blend_user()
        agency = magic_mixer.blend(core.models.Agency, users=[user])
        accounts = magic_mixer.cycle(10).blend(core.models.Account, agency=agency)
        permission = constants.Permission.READ
        magic_mixer.blend(model.EntityPermission, user=user, agency=agency, permission=permission)

        accounts_by_user_permission = core.models.Account.objects.all().filter_by_user(user)
        accounts_by_entity_permission = core.models.Account.objects.all().filter_by_entity_permission(user, permission)

        queryset = helpers.log_differences_and_get_queryset(
            user, permission, accounts_by_user_permission, accounts_by_entity_permission
        )

        self.assertEqual(sorted([x.id for x in accounts]), sorted([x.id for x in queryset]))
        mock_logger.warning.assert_not_called()

    @mock.patch("zemauth.features.entity_permission.helpers.logger")
    def test_query_paginated_for_agency_manager(self, mock_logger):
        paginator = LogDifferencesPaginator(offset=5, limit=2)

        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency, users=[request.user])
        magic_mixer.cycle(10).blend(core.models.Account, agency=agency)
        permission = constants.Permission.READ
        magic_mixer.blend(model.EntityPermission, user=request.user, agency=agency, permission=permission)

        accounts_by_user_permission = core.models.Account.objects.all().filter_by_user(request.user)
        accounts_by_entity_permission = core.models.Account.objects.all().filter_by_entity_permission(
            request.user, permission
        )

        helpers.log_paginated_differences_and_get_queryset(
            request, paginator, permission, accounts_by_user_permission, accounts_by_entity_permission
        )

        mock_logger.warning.assert_not_called()

    @mock.patch("zemauth.features.entity_permission.helpers.logger")
    def test_query_all_for_account_manager(self, mock_logger):
        user = magic_mixer.blend_user()
        agency = magic_mixer.blend(core.models.Agency)
        accounts = magic_mixer.cycle(10).blend(core.models.Account, agency=agency, users=[user])
        permission = constants.Permission.READ
        for account in accounts:
            magic_mixer.blend(model.EntityPermission, user=user, account=account, permission=permission)

        accounts_by_user_permission = core.models.Account.objects.all().filter_by_user(user)
        accounts_by_entity_permission = core.models.Account.objects.all().filter_by_entity_permission(user, permission)

        queryset = helpers.log_differences_and_get_queryset(
            user, permission, accounts_by_user_permission, accounts_by_entity_permission
        )

        self.assertEqual(sorted([x.id for x in accounts]), sorted([x.id for x in queryset]))
        mock_logger.warning.assert_not_called()

    @mock.patch("zemauth.features.entity_permission.helpers.logger")
    def test_query_paginated_for_account_manager(self, mock_logger):
        paginator = LogDifferencesPaginator(offset=5, limit=2)

        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency)
        accounts = magic_mixer.cycle(10).blend(core.models.Account, agency=agency, users=[request.user])
        permission = constants.Permission.READ
        for account in accounts:
            magic_mixer.blend(model.EntityPermission, user=request.user, account=account, permission=permission)

        accounts_by_user_permission = core.models.Account.objects.all().filter_by_user(request.user)
        accounts_by_entity_permission = core.models.Account.objects.all().filter_by_entity_permission(
            request.user, permission
        )

        helpers.log_paginated_differences_and_get_queryset(
            request, paginator, permission, accounts_by_user_permission, accounts_by_entity_permission
        )

        mock_logger.warning.assert_not_called()

    @mock.patch("zemauth.features.entity_permission.helpers.logger")
    def test_query_all_difference_for_agency_manager(self, mock_logger):
        user = magic_mixer.blend_user()
        agency = magic_mixer.blend(core.models.Agency, users=[user])
        accounts = magic_mixer.cycle(10).blend(core.models.Account, agency=agency)
        permission = constants.Permission.READ

        accounts_by_user_permission = core.models.Account.objects.all().filter_by_user(user)
        accounts_by_entity_permission = core.models.Account.objects.all().filter_by_entity_permission(user, permission)

        queryset = helpers.log_differences_and_get_queryset(
            user, permission, accounts_by_user_permission, accounts_by_entity_permission
        )

        self.assertEqual(sorted([x.id for x in accounts]), sorted([x.id for x in queryset]))
        mock_logger.warning.assert_called_once_with(
            helpers.LOG_MESSAGE,
            user_email=user.email,
            permission=permission,
            rows_ids_by_user_permission=set([x.id for x in queryset]),
            rows_ids_by_entity_permission=set(),
            user_permission_queryset_model_name=core.models.Account.__name__,
            entity_permission_queryset_model_name=core.models.Account.__name__,
        )

    @mock.patch("zemauth.features.entity_permission.helpers.logger")
    def test_query_paginated_difference_for_agency_manager(self, mock_logger):
        paginator = LogDifferencesPaginator(offset=5, limit=2)

        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency, users=[request.user])
        magic_mixer.cycle(10).blend(core.models.Account, agency=agency)
        permission = constants.Permission.READ

        accounts_by_user_permission = core.models.Account.objects.all().filter_by_user(request.user)
        accounts_by_entity_permission = core.models.Account.objects.all().filter_by_entity_permission(
            request.user, permission
        )

        queryset = helpers.log_paginated_differences_and_get_queryset(
            request, paginator, permission, accounts_by_user_permission, accounts_by_entity_permission
        )

        mock_logger.warning.assert_called_once_with(
            helpers.LOG_MESSAGE,
            user_email=request.user.email,
            permission=permission,
            rows_ids_by_user_permission=[x.id for x in queryset[5:7]],
            rows_ids_by_entity_permission=[],
            user_permission_queryset_model_name=core.models.Account.__name__,
            entity_permission_queryset_model_name=core.models.Account.__name__,
        )

    @mock.patch("zemauth.features.entity_permission.helpers.logger")
    def test_query_all_difference_for_account_manager(self, mock_logger):
        user = magic_mixer.blend_user()
        agency = magic_mixer.blend(core.models.Agency)
        accounts = magic_mixer.cycle(10).blend(core.models.Account, agency=agency, users=[user])
        permission = constants.Permission.READ

        accounts_by_user_permission = core.models.Account.objects.all().filter_by_user(user)
        accounts_by_entity_permission = core.models.Account.objects.all().filter_by_entity_permission(user, permission)

        queryset = helpers.log_differences_and_get_queryset(
            user, permission, accounts_by_user_permission, accounts_by_entity_permission
        )

        self.assertEqual(sorted([x.id for x in accounts]), sorted([x.id for x in queryset]))
        mock_logger.warning.assert_called_once_with(
            helpers.LOG_MESSAGE,
            user_email=user.email,
            permission=permission,
            rows_ids_by_user_permission=set([x.id for x in queryset]),
            rows_ids_by_entity_permission=set(),
            user_permission_queryset_model_name=core.models.Account.__name__,
            entity_permission_queryset_model_name=core.models.Account.__name__,
        )

    @mock.patch("zemauth.features.entity_permission.helpers.logger")
    def test_query_paginated_difference_for_account_manager(self, mock_logger):
        paginator = LogDifferencesPaginator(offset=5, limit=2)

        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency)
        magic_mixer.cycle(10).blend(core.models.Account, agency=agency, users=[request.user])
        permission = constants.Permission.READ

        accounts_by_user_permission = core.models.Account.objects.all().filter_by_user(request.user)
        accounts_by_entity_permission = core.models.Account.objects.all().filter_by_entity_permission(
            request.user, permission
        )

        queryset = helpers.log_paginated_differences_and_get_queryset(
            request, paginator, permission, accounts_by_user_permission, accounts_by_entity_permission
        )

        mock_logger.warning.assert_called_once_with(
            helpers.LOG_MESSAGE,
            user_email=request.user.email,
            permission=permission,
            rows_ids_by_user_permission=[x.id for x in queryset[5:7]],
            rows_ids_by_entity_permission=[],
            user_permission_queryset_model_name=core.models.Account.__name__,
            entity_permission_queryset_model_name=core.models.Account.__name__,
        )

    @mock.patch("zemauth.features.entity_permission.helpers.logger")
    def test_query_single_for_agency_manager(self, mock_logger):
        user = magic_mixer.blend_user()
        agency = magic_mixer.blend(core.models.Agency, users=[user])
        account = magic_mixer.blend(core.models.Account, agency=agency)
        permission = constants.Permission.READ
        magic_mixer.blend(model.EntityPermission, user=user, agency=agency, permission=permission)

        accounts_by_user_permission = core.models.Account.objects.all().filter_by_user(user)
        accounts_by_entity_permission = core.models.Account.objects.all().filter_by_entity_permission(user, permission)

        queryset = helpers.log_differences_and_get_queryset(
            user, permission, accounts_by_user_permission, accounts_by_entity_permission, account.id
        )

        self.assertEqual(account.id, queryset.get(id=account.id).id)
        mock_logger.warning.assert_not_called()

    @mock.patch("zemauth.features.entity_permission.helpers.logger")
    def test_query_single_for_account_manager(self, mock_logger):
        user = magic_mixer.blend_user()
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency, users=[user])
        permission = constants.Permission.READ
        magic_mixer.blend(model.EntityPermission, user=user, account=account, permission=permission)

        accounts_by_user_permission = core.models.Account.objects.all().filter_by_user(user)
        accounts_by_entity_permission = core.models.Account.objects.all().filter_by_entity_permission(user, permission)

        queryset = helpers.log_differences_and_get_queryset(
            user, permission, accounts_by_user_permission, accounts_by_entity_permission, account.id
        )

        self.assertEqual(account.id, queryset.get(id=account.id).id)
        mock_logger.warning.assert_not_called()

    @mock.patch("zemauth.features.entity_permission.helpers.logger")
    def test_query_single_difference_for_agency_manager(self, mock_logger):
        user = magic_mixer.blend_user()
        agency = magic_mixer.blend(core.models.Agency, users=[user])
        account = magic_mixer.blend(core.models.Account, agency=agency)
        permission = constants.Permission.READ

        accounts_by_user_permission = core.models.Account.objects.all().filter_by_user(user)
        accounts_by_entity_permission = core.models.Account.objects.all().filter_by_entity_permission(user, permission)

        queryset = helpers.log_differences_and_get_queryset(
            user, permission, accounts_by_user_permission, accounts_by_entity_permission, account.id
        )

        self.assertEqual(account.id, queryset.get(id=account.id).id)
        mock_logger.warning.assert_called_once_with(
            helpers.LOG_MESSAGE,
            user_email=user.email,
            permission=permission,
            row_id_by_user_permission=account.id,
            row_id_by_entity_permission=None,
            user_permission_queryset_model_name=core.models.Account.__name__,
            entity_permission_queryset_model_name=core.models.Account.__name__,
        )

    @mock.patch("zemauth.features.entity_permission.helpers.logger")
    def test_query_single_difference_for_account_manager(self, mock_logger):
        user = magic_mixer.blend_user()
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency, users=[user])
        permission = constants.Permission.READ

        accounts_by_user_permission = core.models.Account.objects.all().filter_by_user(user)
        accounts_by_entity_permission = core.models.Account.objects.all().filter_by_entity_permission(user, permission)

        queryset = helpers.log_differences_and_get_queryset(
            user, permission, accounts_by_user_permission, accounts_by_entity_permission, account.id
        )

        self.assertEqual(account.id, queryset.get(id=account.id).id)
        mock_logger.warning.assert_called_once_with(
            helpers.LOG_MESSAGE,
            user_email=user.email,
            permission=permission,
            row_id_by_user_permission=account.id,
            row_id_by_entity_permission=None,
            user_permission_queryset_model_name=core.models.Account.__name__,
            entity_permission_queryset_model_name=core.models.Account.__name__,
        )

    @mock.patch("zemauth.features.entity_permission.helpers.logger")
    def test_query_all_empty_for_agency_manager(self, mock_logger):
        user = magic_mixer.blend_user()
        user.user_permissions.add(self.permission)
        agency = magic_mixer.blend(core.models.Agency, users=[user])
        magic_mixer.cycle(10).blend(core.models.Account, agency=agency)
        permission = constants.Permission.READ

        accounts_by_user_permission = core.models.Account.objects.all().filter_by_user(user)
        accounts_by_entity_permission = core.models.Account.objects.all().filter_by_entity_permission(user, permission)

        queryset = helpers.log_differences_and_get_queryset(
            user, permission, accounts_by_user_permission, accounts_by_entity_permission
        )

        self.assertEqual(list(queryset), [])
        mock_logger.warning.assert_called_once_with(
            helpers.LOG_MESSAGE,
            user_email=user.email,
            permission=permission,
            rows_ids_by_user_permission=set([x.id for x in list(accounts_by_user_permission)]),
            rows_ids_by_entity_permission=set(),
            user_permission_queryset_model_name=core.models.Account.__name__,
            entity_permission_queryset_model_name=core.models.Account.__name__,
        )

    # @mock.patch("zemauth.features.entity_permission.helpers.logger")
    # def test_query_all_empty_for_account_manager(self, mock_logger):
    #     user = magic_mixer.blend_user()
    #     user.user_permissions.add(self.permission)
    #     agency = magic_mixer.blend(core.models.Agency)
    #     magic_mixer.cycle(10).blend(core.models.Account, agency=agency, users=[user])
    #     permission = constants.Permission.READ

    #     accounts_by_user_permission = core.models.Account.objects.all().filter_by_user(user)
    #     accounts_by_entity_permission = core.models.Account.objects.all().filter_by_entity_permission(user, permission)

    #     queryset = helpers.log_differences_and_get_queryset(
    #         user, permission, accounts_by_user_permission, accounts_by_entity_permission
    #     )

    #     self.assertEqual(list(queryset), [])
    #     mock_logger.warning.assert_called_once_with(
    #         helpers.LOG_MESSAGE,
    #         user_email=user.email,
    #         permission=permission,
    #         rows_ids_by_user_permission=set([x.id for x in list(accounts_by_user_permission)]),
    #         rows_ids_by_entity_permission=set(),
    #         user_permission_queryset_model_name=core.models.Account.__name__,
    #         entity_permission_queryset_model_name=core.models.Account.__name__,
    #     )

    @mock.patch("zemauth.features.entity_permission.helpers.logger")
    def test_query_single_not_exists_for_agency_manager(self, mock_logger):
        user = magic_mixer.blend_user()
        user.user_permissions.add(self.permission)
        agency = magic_mixer.blend(core.models.Agency, users=[user])
        account = magic_mixer.blend(core.models.Account, agency=agency)
        permission = constants.Permission.READ

        accounts_by_user_permission = core.models.Account.objects.all().filter_by_user(user)
        accounts_by_entity_permission = core.models.Account.objects.all().filter_by_entity_permission(user, permission)

        queryset = helpers.log_differences_and_get_queryset(
            user, permission, accounts_by_user_permission, accounts_by_entity_permission, account.id
        )

        with self.assertRaises(core.models.Account.DoesNotExist):
            queryset.get(id=account.id)

        mock_logger.warning.assert_called_once_with(
            helpers.LOG_MESSAGE,
            user_email=user.email,
            permission=permission,
            row_id_by_user_permission=account.id,
            row_id_by_entity_permission=None,
            user_permission_queryset_model_name=core.models.Account.__name__,
            entity_permission_queryset_model_name=core.models.Account.__name__,
        )

    @mock.patch("zemauth.features.entity_permission.helpers.logger")
    def test_query_single_not_exists_for_account_manager(self, mock_logger):
        user = magic_mixer.blend_user()
        user.user_permissions.add(self.permission)
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency, users=[user])
        permission = constants.Permission.READ

        accounts_by_user_permission = core.models.Account.objects.all().filter_by_user(user)
        accounts_by_entity_permission = core.models.Account.objects.all().filter_by_entity_permission(user, permission)

        queryset = helpers.log_differences_and_get_queryset(
            user, permission, accounts_by_user_permission, accounts_by_entity_permission, account.id
        )

        with self.assertRaises(core.models.Account.DoesNotExist):
            queryset.get(id=account.id)

        mock_logger.warning.assert_called_once_with(
            helpers.LOG_MESSAGE,
            user_email=user.email,
            permission=permission,
            row_id_by_user_permission=account.id,
            row_id_by_entity_permission=None,
            user_permission_queryset_model_name=core.models.Account.__name__,
            entity_permission_queryset_model_name=core.models.Account.__name__,
        )
