import abc
from typing import Any

import core.models
import core.models.tags.creative
from utils.magic_mixer import magic_mixer


class CreativeTagTestCaseMixin(metaclass=abc.ABCMeta):
    def test_set_creative_tags(self):
        agency: core.models.Agency = magic_mixer.blend(core.models.Agency)
        account: core.models.Account = magic_mixer.blend(core.models.Account, agency=agency)

        model_with_agency_scope: Any = self._get_model_with_agency_scope(agency)
        model_with_account_scope: Any = self._get_model_with_account_scope(account)

        if model_with_agency_scope is not None:
            self._test_for_new(model_with_agency_scope)
            self._test_for_existing(model_with_agency_scope)
            self._test_for_mixed(model_with_agency_scope)
            self._test_for_invalid_agency(model_with_agency_scope)
            self._test_for_invalid_account(model_with_agency_scope)

        if model_with_account_scope is not None:
            self._test_for_new(model_with_account_scope)
            self._test_for_existing(model_with_account_scope)
            self._test_for_mixed(model_with_account_scope)
            self._test_for_invalid_agency(model_with_account_scope)
            self._test_for_invalid_account(model_with_account_scope)

    @abc.abstractmethod
    def _get_model_with_agency_scope(self, agency: core.models.Agency) -> Any:
        """
        Return model instance connected to agency in order to test set_tags.
        Return None to skip tests.
        :param agency: core.models.Agency
        :return: model (with with agency scope)
        """
        raise NotImplementedError("Not implemented.")

    @abc.abstractmethod
    def _get_model_with_account_scope(self, account: core.models.Account) -> Any:
        """
        Return model instance connected to account in order to test set_tags.
        Return None to skip tests.
        :param account: core.models.Account
        :return: model (with with account scope)
        """
        raise NotImplementedError("Not implemented.")

    def _test_for_new(self, instance):
        instance.clear_creative_tags()
        self.assertEqual(instance.get_creative_tags(), [])

        data = ["tag_1", "tag_2", "tag_3"]

        tags_count = core.models.tags.CreativeTag.objects.filter(
            name__in=data, agency=instance.agency, account=instance.account
        ).count()
        self.assertEqual(tags_count, 0)

        instance.set_creative_tags(None, data)

        count = core.models.tags.CreativeTag.objects.filter(
            name__in=data, agency=instance.agency, account=instance.account
        ).count()
        self.assertEqual(count, len(data))

        self.assertCountEqual([x.name for x in instance.get_creative_tags()], data)

    def _test_for_existing(self, instance):
        instance.clear_creative_tags()
        self.assertEqual(instance.get_creative_tags(), [])

        tag_4 = core.models.tags.CreativeTag.objects.create(
            name="tag_4", agency=instance.agency, account=instance.account
        )
        tag_5 = core.models.tags.CreativeTag.objects.create(
            name="tag_5", agency=instance.agency, account=instance.account
        )
        tag_6 = core.models.tags.CreativeTag.objects.create(
            name="tag_6", agency=instance.agency, account=instance.account
        )

        data = [tag_4, tag_5, tag_6]

        count = core.models.tags.CreativeTag.objects.filter(
            name__in=[x.name for x in data], agency=instance.agency, account=instance.account
        ).count()
        self.assertEqual(count, len(data))

        instance.set_creative_tags(None, data)

        self.assertCountEqual([x.id for x in instance.get_creative_tags()], [x.id for x in data])

    def _test_for_mixed(self, instance):
        instance.clear_creative_tags()
        self.assertEqual(instance.get_creative_tags(), [])

        tag_7 = core.models.tags.CreativeTag.objects.create(
            name="tag_7", agency=instance.agency, account=instance.account
        )
        tag_8 = core.models.tags.CreativeTag.objects.create(
            name="tag_8", agency=instance.agency, account=instance.account
        )

        data = [tag_7.name, tag_8.name, "tag_9"]

        tags_count = core.models.tags.CreativeTag.objects.filter(
            name__in=data, agency=instance.agency, account=instance.account
        ).count()
        self.assertEqual(tags_count, 2)

        instance.set_creative_tags(None, data)

        tags_count = core.models.tags.CreativeTag.objects.filter(
            name__in=data, agency=instance.agency, account=instance.account
        ).count()
        self.assertEqual(tags_count, 3)

        self.assertCountEqual([x.name for x in instance.get_creative_tags()], data)

    def _test_for_invalid_agency(self, instance):
        instance.clear_creative_tags()
        self.assertEqual(instance.get_creative_tags(), [])

        invalid_agency: core.models.Agency = magic_mixer.blend(core.models.Agency)

        tag_10 = core.models.tags.CreativeTag.objects.create(name="tag_10", agency=invalid_agency)

        data = [tag_10]

        with self.assertRaises(core.models.tags.creative.InvalidAgency):
            instance.set_creative_tags(None, data)

    def _test_for_invalid_account(self, instance):
        instance.clear_creative_tags()
        self.assertEqual(instance.get_creative_tags(), [])

        invalid_account: core.models.Account = magic_mixer.blend(core.models.Account)

        tag_11 = core.models.tags.CreativeTag.objects.create(name="tag_11", account=invalid_account)

        data = [tag_11]

        with self.assertRaises(core.models.tags.creative.InvalidAccount):
            instance.set_creative_tags(None, data)
