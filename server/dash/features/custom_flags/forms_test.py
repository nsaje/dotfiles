from django.test import TestCase
from mock import Mock

from . import model, forms
from zemauth.models import User
from dash.models import Account


class CustomFlagsFormMixinTest(TestCase):
    fixtures = ["test_models.yaml"]

    def setUp(self):
        self.advanced_custom_flag = model.CustomFlag(
            type="int", name="advanced custom flag name", id="advanced custom flag ID", advanced=True
        )
        self.basic_custom_flag = model.CustomFlag(
            type="int", name="basic custom flag name", id="basic custom flag ID", advanced=False
        )
        self.advanced_custom_flag.save()
        self.basic_custom_flag.save()
        self.account = Account.objects.get(id=1)
        self.account.custom_flags = {self.advanced_custom_flag.id: 0, self.basic_custom_flag.id: 0}
        self.account.save(None)

        self.request = Mock()

    def test_admin_edit_advanced_custom_flags_with_permissions(self):
        admin_user = User.objects.get(id=1)
        self.assertTrue(admin_user.has_perm("zemauth.can_edit_advanced_custom_flags"))

        custom_flags_form = forms.CustomFlagsFormMixin(
            data={"custom_flags_0": 0, "custom_flags_1": 1},
            files=None,
            auto_id="id_%s",
            prefix=None,
            initial={"custom_flags": self.account.custom_flags},
        )

        #  There is an instance variable "instance" set by the ***Admin view in get_form(). It is set here
        custom_flags_form.instance = self.account
        #  The **Admin view in get_form() also passes the request object
        self.request.user = admin_user
        custom_flags_form.request = self.request

        self.assertTrue(custom_flags_form.is_valid())
        self.assertEqual(
            custom_flags_form.clean_custom_flags(), {"basic custom flag ID": 0, "advanced custom flag ID": 1}
        )
        self.assertEqual(
            custom_flags_form.cleaned_data["custom_flags"], {"basic custom flag ID": 0, "advanced custom flag ID": 1}
        )

    def test_non_admin_edit_advanced_custom_flags_without_permissions(self):
        non_admin_user = User.objects.get(id=2)
        self.assertFalse(non_admin_user.has_perm("zemauth.can_edit_advanced_custom_flags"))
        custom_flags_form = forms.CustomFlagsFormMixin(
            data={"custom_flags_0": 0, "custom_flags_1": 1},
            files=None,
            auto_id="id_%s",
            prefix=None,
            initial={"custom_flags": self.account.custom_flags},
        )

        #  There is an instance variable "instance" set by the ***Admin view in get_form(). It is set here
        custom_flags_form.instance = self.account
        #  The **Admin view in get_form() also passes the request object
        self.request.user = non_admin_user
        custom_flags_form.request = self.request

        self.assertFalse(custom_flags_form.is_valid())
        self.assertEqual(custom_flags_form.has_error("custom_flags"), True)
        self.assertEqual(
            custom_flags_form.errors["custom_flags"],
            ["Advanced Flags (advanced custom flag name) can only be modified by admin."],
        )

    def test_non_admin_edit_basic_custom_flags(self):
        non_admin_user = User.objects.get(id=2)
        self.assertFalse(non_admin_user.has_perm("zemauth.can_edit_advanced_custom_flags"))
        custom_flags_form = forms.CustomFlagsFormMixin(
            data={"custom_flags_0": 1, "custom_flags_1": 0},
            files=None,
            auto_id="id_%s",
            prefix=None,
            initial={"custom_flags": self.account.custom_flags},
        )

        #  There is an instance variable "instance" set by the ***Admin view in get_form(). It is set here
        custom_flags_form.instance = self.account
        #  The **Admin view in get_form() also passes the request object
        self.request.user = non_admin_user
        custom_flags_form.request = self.request
        self.assertTrue(custom_flags_form.is_valid())
        self.assertEqual(
            custom_flags_form.clean_custom_flags(), {"basic custom flag ID": 1, "advanced custom flag ID": 0}
        )
        self.assertEqual(
            custom_flags_form.cleaned_data["custom_flags"], {"basic custom flag ID": 1, "advanced custom flag ID": 0}
        )
