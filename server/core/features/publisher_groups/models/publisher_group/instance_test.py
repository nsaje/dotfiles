from unittest import mock

import core.features.publisher_groups
import core.models
from utils.base_test_case import BaseTestCase
from utils.base_test_case import FutureBaseTestCase
from utils.exc import ValidationError
from utils.magic_mixer import get_request_mock
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class LegacyPublisherGroupInstanceTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.request = get_request_mock(self.user)

    def test_create_with_agency(self):
        agency = self.mix_agency(self.request.user, permissions=[Permission.READ, Permission.WRITE])
        name = "Test publisher group"

        publisher_group = core.features.publisher_groups.PublisherGroup.objects.create(
            self.request, name, agency=agency
        )

        self.assertEqual(publisher_group.name, name)
        self.assertEqual(publisher_group.agency, agency)
        self.assertEqual(publisher_group.account, None)

    def test_create_with_account(self):
        account = self.mix_account(self.request.user, permissions=[Permission.READ, Permission.WRITE])
        name = "Test publisher group"

        publisher_group = core.features.publisher_groups.PublisherGroup.objects.create(
            self.request, name, account=account
        )

        self.assertEqual(publisher_group.name, name)
        self.assertEqual(publisher_group.agency, None)
        self.assertEqual(publisher_group.account, account)

    def test_create_global(self):
        name = "Test publisher group"

        publisher_group = core.features.publisher_groups.PublisherGroup.objects.create(self.request, name)

        self.assertEqual(publisher_group.name, name)
        self.assertEqual(publisher_group.agency, None)
        self.assertEqual(publisher_group.account, None)

    def test_create_agency_and_account(self):
        agency = self.mix_agency(self.request.user, permissions=[Permission.READ, Permission.WRITE])
        account = magic_mixer.blend(core.models.Account, agency=agency)
        name = "Test publisher group"

        with self.assertRaises(ValidationError):
            core.features.publisher_groups.PublisherGroup.objects.create(
                self.request, name, agency=agency, account=account
            )

    def test_update(self):
        agency = self.mix_agency(self.request.user, permissions=[Permission.READ, Permission.WRITE])
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, agency=agency, name=name)

        self.assertEqual(publisher_group.name, name)
        self.assertEqual(publisher_group.agency, agency)
        self.assertEqual(publisher_group.account, None)

        updated_name = "Test publisher group UPDATED"

        publisher_group.name = updated_name
        publisher_group.save(self.request)

        self.assertEqual(publisher_group.name, updated_name)

    def test_update_valid_account(self):
        agency = self.mix_agency(self.request.user, permissions=[Permission.READ, Permission.WRITE])
        account = magic_mixer.blend(core.models.Account, agency=agency)
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, agency=agency, name=name)

        campaign = magic_mixer.blend(core.models.Campaign, account=account, default_whitelist=publisher_group)
        adgroup = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        adgroup.settings.update(request=self.request, whitelist_publisher_groups=[publisher_group.id])

        self.assertEqual(publisher_group.name, name)
        self.assertEqual(publisher_group.agency, agency)
        self.assertEqual(publisher_group.account, None)

        publisher_group.agency = None
        publisher_group.account = account

        publisher_group.save(self.request)

        self.assertEqual(publisher_group.agency, None)
        self.assertEqual(publisher_group.account, account)

    def test_update_invalid_account_default_whitelist(self):
        agency = self.mix_agency(self.request.user, permissions=[Permission.READ, Permission.WRITE])
        account = magic_mixer.blend(core.models.Account, agency=agency)
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, agency=agency, name=name)

        magic_mixer.blend(core.models.Campaign, account=account, default_whitelist=publisher_group)

        self.assertEqual(publisher_group.name, name)
        self.assertEqual(publisher_group.agency, agency)
        self.assertEqual(publisher_group.account, None)

        new_account = self.mix_account(self.request.user, permissions=[Permission.READ, Permission.WRITE])

        publisher_group.agency = None
        publisher_group.account = new_account

        with self.assertRaises(ValidationError):
            publisher_group.save(self.request)

    def test_update_invalid_account_whitelist_publisher_groups(self):
        agency = self.mix_agency(self.request.user, permissions=[Permission.READ, Permission.WRITE])
        account = magic_mixer.blend(core.models.Account, agency=agency)
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, agency=agency, name=name)

        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        adgroup = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        adgroup.settings.update(request=self.request, whitelist_publisher_groups=[publisher_group.id])

        self.assertEqual(publisher_group.name, name)
        self.assertEqual(publisher_group.agency, agency)
        self.assertEqual(publisher_group.account, None)

        new_account = self.mix_account(self.request.user, permissions=[Permission.READ, Permission.WRITE])

        publisher_group.agency = None
        publisher_group.account = new_account

        with self.assertRaises(ValidationError):
            publisher_group.save(self.request)

    def test_update_invalid_account_default_blacklist(self):
        agency = self.mix_agency(self.request.user, permissions=[Permission.READ, Permission.WRITE])
        account = magic_mixer.blend(core.models.Account, agency=agency)
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, agency=agency, name=name)

        magic_mixer.blend(core.models.Campaign, account=account, default_blacklist=publisher_group)

        self.assertEqual(publisher_group.name, name)
        self.assertEqual(publisher_group.agency, agency)
        self.assertEqual(publisher_group.account, None)

        new_account = self.mix_account(self.request.user, permissions=[Permission.READ, Permission.WRITE])

        publisher_group.agency = None
        publisher_group.account = new_account

        with self.assertRaises(ValidationError):
            publisher_group.save(self.request)

    def test_update_invalid_account_blacklist_publisher_groups(self):
        agency = self.mix_agency(self.request.user, permissions=[Permission.READ, Permission.WRITE])
        account = magic_mixer.blend(core.models.Account, agency=agency)
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, agency=agency, name=name)

        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        adgroup = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        adgroup.settings.update(request=self.request, blacklist_publisher_groups=[publisher_group.id])

        self.assertEqual(publisher_group.name, name)
        self.assertEqual(publisher_group.agency, agency)
        self.assertEqual(publisher_group.account, None)

        new_account = self.mix_account(self.request.user, permissions=[Permission.READ, Permission.WRITE])

        publisher_group.agency = None
        publisher_group.account = new_account

        with self.assertRaises(ValidationError):
            publisher_group.save(self.request)

    def test_update_valid_agency(self):
        agency = self.mix_agency(self.request.user, permissions=[Permission.READ, Permission.WRITE])
        account = magic_mixer.blend(core.models.Account, agency=agency)
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account, name=name)

        campaign = magic_mixer.blend(core.models.Campaign, account=account, default_whitelist=publisher_group)
        adgroup = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        adgroup.settings.update(request=self.request, whitelist_publisher_groups=[publisher_group.id])

        self.assertEqual(publisher_group.name, name)
        self.assertEqual(publisher_group.agency, None)
        self.assertEqual(publisher_group.account, account)

        publisher_group.agency = agency
        publisher_group.account = None

        publisher_group.save(self.request)

        self.assertEqual(publisher_group.agency, agency)
        self.assertEqual(publisher_group.account, None)

    def test_update_invalid_agency_default_whitelist(self):
        agency = self.mix_agency(self.request.user, permissions=[Permission.READ, Permission.WRITE])
        account = magic_mixer.blend(core.models.Account, agency=agency)
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account, name=name)

        magic_mixer.blend(core.models.Campaign, account=account, default_whitelist=publisher_group)

        self.assertEqual(publisher_group.name, name)
        self.assertEqual(publisher_group.agency, None)
        self.assertEqual(publisher_group.account, account)

        new_agency = self.mix_agency(self.request.user, permissions=[Permission.READ, Permission.WRITE])

        publisher_group.agency = new_agency
        publisher_group.account = None

        with self.assertRaises(ValidationError):
            publisher_group.save(self.request)

    def test_update_invalid_agency_whitelist_publisher_groups(self):
        agency = self.mix_agency(self.request.user, permissions=[Permission.READ, Permission.WRITE])
        account = magic_mixer.blend(core.models.Account, agency=agency)
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account, name=name)

        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        adgroup = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        adgroup.settings.update(request=self.request, whitelist_publisher_groups=[publisher_group.id])

        self.assertEqual(publisher_group.name, name)
        self.assertEqual(publisher_group.agency, None)
        self.assertEqual(publisher_group.account, account)

        new_agency = self.mix_agency(self.request.user, permissions=[Permission.READ, Permission.WRITE])

        publisher_group.agency = new_agency
        publisher_group.account = None

        with self.assertRaises(ValidationError):
            publisher_group.save(self.request)

    def test_update_invalid_agency_default_blacklist(self):
        agency = self.mix_agency(self.request.user, permissions=[Permission.READ, Permission.WRITE])
        account = magic_mixer.blend(core.models.Account, agency=agency)
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account, name=name)

        magic_mixer.blend(core.models.Campaign, account=account, default_blacklist=publisher_group)

        self.assertEqual(publisher_group.name, name)
        self.assertEqual(publisher_group.agency, None)
        self.assertEqual(publisher_group.account, account)

        new_agency = self.mix_agency(self.request.user, permissions=[Permission.READ, Permission.WRITE])

        publisher_group.agency = new_agency
        publisher_group.account = None

        with self.assertRaises(ValidationError):
            publisher_group.save(self.request)

    def test_update_invalid_agency_blacklist_publisher_groups(self):
        agency = self.mix_agency(self.request.user, permissions=[Permission.READ, Permission.WRITE])
        account = magic_mixer.blend(core.models.Account, agency=agency)
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account, name=name)

        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        adgroup = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        adgroup.settings.update(request=self.request, blacklist_publisher_groups=[publisher_group.id])

        self.assertEqual(publisher_group.name, name)
        self.assertEqual(publisher_group.agency, None)
        self.assertEqual(publisher_group.account, account)

        new_agency = self.mix_agency(self.request.user, permissions=[Permission.READ, Permission.WRITE])

        publisher_group.agency = new_agency
        publisher_group.account = None

        with self.assertRaises(ValidationError):
            publisher_group.save(self.request)

    @mock.patch(
        "core.features.publisher_groups.get_publisher_group_connections", mock.MagicMock(return_value=[], autospec=True)
    )
    def test_delete_unused_publisher_group(self):
        agency = self.mix_agency(self.request.user, permissions=[Permission.READ, Permission.WRITE])
        account = magic_mixer.blend(core.models.Account, agency=agency)
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account, name=name)

        try:
            publisher_group.delete(self.request)
        except ValidationError:
            self.fail("delete() raised ValidationError unexpectedly!")

    @mock.patch(
        "core.features.publisher_groups.get_publisher_group_connections",
        mock.MagicMock(
            return_value=[{"id": 766811, "name": "Mobile", "location": "adGroupWhitelist", "user_access": True}],
            autospec=True,
        ),
    )
    def test_delete_used_publisher_group(self):
        agency = self.mix_agency(self.request.user, permissions=[Permission.READ, Permission.WRITE])
        account = magic_mixer.blend(core.models.Account, agency=agency)
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account, name=name)

        with self.assertRaises(ValidationError) as err:
            publisher_group.delete(self.request)
        self.assertEqual(
            'This publisher group can not be deleted, because it is whitelisted in ad group "Mobile".',
            str(err.exception),
        )

    @mock.patch(
        "core.features.publisher_groups.get_publisher_group_connections",
        mock.MagicMock(
            return_value=[{"id": 766811, "name": "Mobile", "location": "adGroupWhitelist", "user_access": False}],
            autospec=True,
        ),
    )
    def test_delete_publisher_group_with_other_usage(self):
        agency = self.mix_agency(self.request.user, permissions=[Permission.READ, Permission.WRITE])
        account = magic_mixer.blend(core.models.Account, agency=agency)
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account, name=name)

        with self.assertRaises(ValidationError) as err:
            publisher_group.delete(self.request)
        self.assertEqual(
            "This publisher group can not be deleted, because it is used in 1 locations.", str(err.exception)
        )

    @mock.patch(
        "core.features.publisher_groups.get_publisher_group_connections",
        mock.MagicMock(
            return_value=[
                {"id": 766811, "name": "Mobile", "location": "adGroupWhitelist", "user_access": True},
                {"id": 766812, "name": "Desktop", "location": "adGroupWhitelist", "user_access": False},
            ],
            autospec=True,
        ),
    )
    def test_delete_publisher_group_with_user_and_other_usages(self):
        agency = self.mix_agency(self.request.user, permissions=[Permission.READ, Permission.WRITE])
        account = magic_mixer.blend(core.models.Account, agency=agency)
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account, name=name)

        with self.assertRaises(ValidationError) as err:
            publisher_group.delete(self.request)
        self.assertEqual(
            'This publisher group can not be deleted, because it is whitelisted in ad group "Mobile", used in 1 other locations.',
            str(err.exception),
        )


class PublisherGroupInstanceTestCase(FutureBaseTestCase, LegacyPublisherGroupInstanceTestCase):
    pass
