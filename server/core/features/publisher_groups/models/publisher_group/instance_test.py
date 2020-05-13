from unittest import mock

from django.test import TestCase

import core.features.publisher_groups
import core.models
from utils.exc import ValidationError
from utils.magic_mixer import magic_mixer


class PublisherGroupInstanceTestCase(TestCase):
    def test_create_with_agency(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency, users=[request.user])
        name = "Test publisher group"

        publisher_group = core.features.publisher_groups.PublisherGroup.objects.create(request, name, agency=agency)

        self.assertEqual(publisher_group.name, name)
        self.assertEqual(publisher_group.agency, agency)
        self.assertEqual(publisher_group.account, None)

    def test_create_with_account(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.models.Account, users=[request.user])
        name = "Test publisher group"

        publisher_group = core.features.publisher_groups.PublisherGroup.objects.create(request, name, account=account)

        self.assertEqual(publisher_group.name, name)
        self.assertEqual(publisher_group.agency, None)
        self.assertEqual(publisher_group.account, account)

    def test_create_global(self):
        request = magic_mixer.blend_request_user()
        name = "Test publisher group"

        publisher_group = core.features.publisher_groups.PublisherGroup.objects.create(request, name)

        self.assertEqual(publisher_group.name, name)
        self.assertEqual(publisher_group.agency, None)
        self.assertEqual(publisher_group.account, None)

    def test_create_agency_and_account(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency, users=[request.user])
        account = magic_mixer.blend(core.models.Account, agency=agency, users=[request.user])
        name = "Test publisher group"

        with self.assertRaises(ValidationError):
            core.features.publisher_groups.PublisherGroup.objects.create(request, name, agency=agency, account=account)

    def test_update(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency, users=[request.user])
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, agency=agency, name=name)

        self.assertEqual(publisher_group.name, name)
        self.assertEqual(publisher_group.agency, agency)
        self.assertEqual(publisher_group.account, None)

        updated_name = "Test publisher group UPDATED"

        publisher_group.name = updated_name
        publisher_group.save(request)

        self.assertEqual(publisher_group.name, updated_name)

    def test_update_valid_account(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency, users=[request.user])
        account = magic_mixer.blend(core.models.Account, users=[request.user], agency=agency)
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, agency=agency, name=name)

        campaign = magic_mixer.blend(
            core.models.Campaign, account=account, users=[request.user], default_whitelist=publisher_group
        )
        adgroup = magic_mixer.blend(core.models.AdGroup, campaign=campaign, users=[request.user])
        adgroup.settings.update(request=request, whitelist_publisher_groups=[publisher_group.id])

        self.assertEqual(publisher_group.name, name)
        self.assertEqual(publisher_group.agency, agency)
        self.assertEqual(publisher_group.account, None)

        publisher_group.agency = None
        publisher_group.account = account

        publisher_group.save(request)

        self.assertEqual(publisher_group.agency, None)
        self.assertEqual(publisher_group.account, account)

    def test_update_invalid_account_default_whitelist(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency, users=[request.user])
        account = magic_mixer.blend(core.models.Account, users=[request.user], agency=agency)
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, agency=agency, name=name)

        magic_mixer.blend(
            core.models.Campaign, account=account, users=[request.user], default_whitelist=publisher_group
        )

        self.assertEqual(publisher_group.name, name)
        self.assertEqual(publisher_group.agency, agency)
        self.assertEqual(publisher_group.account, None)

        new_account = magic_mixer.blend(core.models.Account, users=[request.user])

        publisher_group.agency = None
        publisher_group.account = new_account

        with self.assertRaises(ValidationError):
            publisher_group.save(request)

    def test_update_invalid_account_whitelist_publisher_groups(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency, users=[request.user])
        account = magic_mixer.blend(core.models.Account, users=[request.user], agency=agency)
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, agency=agency, name=name)

        campaign = magic_mixer.blend(core.models.Campaign, account=account, users=[request.user])
        adgroup = magic_mixer.blend(core.models.AdGroup, campaign=campaign, users=[request.user])
        adgroup.settings.update(request=request, whitelist_publisher_groups=[publisher_group.id])

        self.assertEqual(publisher_group.name, name)
        self.assertEqual(publisher_group.agency, agency)
        self.assertEqual(publisher_group.account, None)

        new_account = magic_mixer.blend(core.models.Account, users=[request.user])

        publisher_group.agency = None
        publisher_group.account = new_account

        with self.assertRaises(ValidationError):
            publisher_group.save(request)

    def test_update_invalid_account_default_blacklist(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency, users=[request.user])
        account = magic_mixer.blend(core.models.Account, users=[request.user], agency=agency)
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, agency=agency, name=name)

        magic_mixer.blend(
            core.models.Campaign, account=account, users=[request.user], default_blacklist=publisher_group
        )

        self.assertEqual(publisher_group.name, name)
        self.assertEqual(publisher_group.agency, agency)
        self.assertEqual(publisher_group.account, None)

        new_account = magic_mixer.blend(core.models.Account, users=[request.user])

        publisher_group.agency = None
        publisher_group.account = new_account

        with self.assertRaises(ValidationError):
            publisher_group.save(request)

    def test_update_invalid_account_blacklist_publisher_groups(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency, users=[request.user])
        account = magic_mixer.blend(core.models.Account, users=[request.user], agency=agency)
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, agency=agency, name=name)

        campaign = magic_mixer.blend(core.models.Campaign, account=account, users=[request.user])
        adgroup = magic_mixer.blend(core.models.AdGroup, campaign=campaign, users=[request.user])
        adgroup.settings.update(request=request, blacklist_publisher_groups=[publisher_group.id])

        self.assertEqual(publisher_group.name, name)
        self.assertEqual(publisher_group.agency, agency)
        self.assertEqual(publisher_group.account, None)

        new_account = magic_mixer.blend(core.models.Account, users=[request.user])

        publisher_group.agency = None
        publisher_group.account = new_account

        with self.assertRaises(ValidationError):
            publisher_group.save(request)

    def test_update_valid_agency(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency, users=[request.user])
        account = magic_mixer.blend(core.models.Account, users=[request.user], agency=agency)
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account, name=name)

        campaign = magic_mixer.blend(
            core.models.Campaign, account=account, users=[request.user], default_whitelist=publisher_group
        )
        adgroup = magic_mixer.blend(core.models.AdGroup, campaign=campaign, users=[request.user])
        adgroup.settings.update(request=request, whitelist_publisher_groups=[publisher_group.id])

        self.assertEqual(publisher_group.name, name)
        self.assertEqual(publisher_group.agency, None)
        self.assertEqual(publisher_group.account, account)

        publisher_group.agency = agency
        publisher_group.account = None

        publisher_group.save(request)

        self.assertEqual(publisher_group.agency, agency)
        self.assertEqual(publisher_group.account, None)

    def test_update_invalid_agency_default_whitelist(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency, users=[request.user])
        account = magic_mixer.blend(core.models.Account, users=[request.user], agency=agency)
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account, name=name)

        magic_mixer.blend(
            core.models.Campaign, account=account, users=[request.user], default_whitelist=publisher_group
        )

        self.assertEqual(publisher_group.name, name)
        self.assertEqual(publisher_group.agency, None)
        self.assertEqual(publisher_group.account, account)

        new_agency = magic_mixer.blend(core.models.Agency, users=[request.user])

        publisher_group.agency = new_agency
        publisher_group.account = None

        with self.assertRaises(ValidationError):
            publisher_group.save(request)

    def test_update_invalid_agency_whitelist_publisher_groups(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency, users=[request.user])
        account = magic_mixer.blend(core.models.Account, users=[request.user], agency=agency)
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account, name=name)

        campaign = magic_mixer.blend(core.models.Campaign, account=account, users=[request.user])
        adgroup = magic_mixer.blend(core.models.AdGroup, campaign=campaign, users=[request.user])
        adgroup.settings.update(request=request, whitelist_publisher_groups=[publisher_group.id])

        self.assertEqual(publisher_group.name, name)
        self.assertEqual(publisher_group.agency, None)
        self.assertEqual(publisher_group.account, account)

        new_agency = magic_mixer.blend(core.models.Agency, users=[request.user])

        publisher_group.agency = new_agency
        publisher_group.account = None

        with self.assertRaises(ValidationError):
            publisher_group.save(request)

    def test_update_invalid_agency_default_blacklist(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency, users=[request.user])
        account = magic_mixer.blend(core.models.Account, users=[request.user], agency=agency)
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account, name=name)

        magic_mixer.blend(
            core.models.Campaign, account=account, users=[request.user], default_blacklist=publisher_group
        )

        self.assertEqual(publisher_group.name, name)
        self.assertEqual(publisher_group.agency, None)
        self.assertEqual(publisher_group.account, account)

        new_agency = magic_mixer.blend(core.models.Agency, users=[request.user])

        publisher_group.agency = new_agency
        publisher_group.account = None

        with self.assertRaises(ValidationError):
            publisher_group.save(request)

    def test_update_invalid_agency_blacklist_publisher_groups(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency, users=[request.user])
        account = magic_mixer.blend(core.models.Account, users=[request.user], agency=agency)
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account, name=name)

        campaign = magic_mixer.blend(core.models.Campaign, account=account, users=[request.user])
        adgroup = magic_mixer.blend(core.models.AdGroup, campaign=campaign, users=[request.user])
        adgroup.settings.update(request=request, blacklist_publisher_groups=[publisher_group.id])

        self.assertEqual(publisher_group.name, name)
        self.assertEqual(publisher_group.agency, None)
        self.assertEqual(publisher_group.account, account)

        new_agency = magic_mixer.blend(core.models.Agency, users=[request.user])

        publisher_group.agency = new_agency
        publisher_group.account = None

        with self.assertRaises(ValidationError):
            publisher_group.save(request)

    @mock.patch(
        "core.features.publisher_groups.get_publisher_group_connections", mock.MagicMock(return_value=[], autospec=True)
    )
    def test_delete_unused_publisher_group(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency, users=[request.user])
        account = magic_mixer.blend(core.models.Account, users=[request.user], agency=agency)
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account, name=name)

        try:
            publisher_group.delete(request)
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
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency, users=[request.user])
        account = magic_mixer.blend(core.models.Account, users=[request.user], agency=agency)
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account, name=name)

        with self.assertRaises(ValidationError) as err:
            publisher_group.delete(request)
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
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency, users=[request.user])
        account = magic_mixer.blend(core.models.Account, users=[request.user], agency=agency)
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account, name=name)

        with self.assertRaises(ValidationError) as err:
            publisher_group.delete(request)
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
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency, users=[request.user])
        account = magic_mixer.blend(core.models.Account, users=[request.user], agency=agency)
        name = "Test publisher group"

        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account, name=name)

        with self.assertRaises(ValidationError) as err:
            publisher_group.delete(request)
        self.assertEqual(
            'This publisher group can not be deleted, because it is whitelisted in ad group "Mobile", used in 1 other locations.',
            str(err.exception),
        )
