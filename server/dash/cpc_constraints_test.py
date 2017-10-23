from decimal import Decimal

from django import test, forms

from dash import cpc_constraints
from dash import models, constants
from zemauth.models import User


class CpcConstraintsTestCase(test.TestCase):
    fixtures = ['test_models.yaml']

    def test_create(self):
        with self.assertRaises(AssertionError):
            cpc_constraints.create(min_cpc=Decimal('0.05'))

        cpc_constraints.create(constraint_type=constants.CpcConstraintType.OUTBRAIN_BLACKLIST,
                               min_cpc=Decimal('0.05'), agency_id=1)
        self.assertTrue(models.CpcConstraint.objects.filter(
            agency_id=1,
            constraint_type=constants.CpcConstraintType.OUTBRAIN_BLACKLIST,
            min_cpc=Decimal('0.05')
        ))
        cpc_constraints.create(min_cpc=Decimal('0.05'), account_id=1)
        self.assertTrue(models.CpcConstraint.objects.filter(
            account_id=1,
            constraint_type=constants.CpcConstraintType.MANUAL,
            min_cpc=Decimal('0.05')
        ))
        cpc_constraints.create(max_cpc=Decimal('2.55'), campaign_id=1)
        self.assertTrue(models.CpcConstraint.objects.filter(
            campaign_id=1,
            constraint_type=constants.CpcConstraintType.MANUAL,
            max_cpc=Decimal('2.55')
        ))
        cpc_constraints.create(min_cpc=Decimal('0.05'), max_cpc=Decimal('1.65'), ad_group_id=1)
        self.assertTrue(models.CpcConstraint.objects.filter(
            ad_group_id=1,
            constraint_type=constants.CpcConstraintType.MANUAL,
            min_cpc=Decimal('0.05'),
            max_cpc=Decimal('1.65'),
        ))
        cpc_constraints.create(min_cpc=Decimal('0.05'), source_id=1, campaign_id=1)
        self.assertTrue(models.CpcConstraint.objects.filter(
            campaign_id=1,
            source_id=1,
            constraint_type=constants.CpcConstraintType.MANUAL,
            min_cpc=Decimal('0.05'),
        ))

    def test_create_settings_validation(self):
        with self.assertRaises(forms.ValidationError) as err1:
            cpc_constraints.create(min_cpc=Decimal('0.65'), account_id=1, source_id=1)
        self.assertEqual(err1.exception.messages[0],
                         'Source AdBlade Bid CPC has to be above $0.65 on all ad groups. Please contact Customer Success Team.')
        with self.assertRaises(forms.ValidationError) as err2:
            cpc_constraints.create(max_cpc=Decimal('0.05'), campaign_id=1, source_id=1)
        self.assertEqual(err2.exception.messages[0],
                         'Source AdBlade Bid CPC has to be under $0.05 on all ad groups. Please contact Customer Success Team.')
        with self.assertRaises(forms.ValidationError) as err3:
            cpc_constraints.create(min_cpc=Decimal('0.65'), max_cpc=Decimal('1.65'), account_id=1)
        self.assertEqual(err3.exception.messages[0],
                         'Bid CPC has to be between $0.65 and $1.65 on all ad groups. Please contact Customer Success Team.')

    def test_enforce_account_rule_on_settings(self):
        settings = models.AdGroupSource.objects.get(
            ad_group_id=1,
            source_id=1
        ).get_current_settings()
        self.assertEqual(settings.cpc_cc, Decimal('0.12'))
        settings = models.AdGroupSource.objects.get(
            ad_group_id=4,
            source_id=1
        ).get_current_settings()
        self.assertEqual(settings.cpc_cc, Decimal('0.12'))

        cpc_constraints.enforce_rule(min_cpc=Decimal('0.65'), account_id=1, source_id=1)

        settings = models.AdGroupSource.objects.get(
            ad_group_id=1,
            source_id=1
        ).get_current_settings()
        self.assertEqual(settings.cpc_cc, Decimal('0.65'))
        settings = models.AdGroupSource.objects.get(
            ad_group_id=4,
            source_id=1
        ).get_current_settings()
        self.assertEqual(settings.cpc_cc, Decimal('0.65'))

    def test_enforce_ad_group_rule_on_settings(self):
        settings = models.AdGroupSource.objects.get(
            ad_group_id=1,
            source_id=1
        ).get_current_settings()
        self.assertEqual(settings.cpc_cc, Decimal('0.12'))
        settings = models.AdGroupSource.objects.get(
            ad_group_id=4,
            source_id=1
        ).get_current_settings()
        self.assertEqual(settings.cpc_cc, Decimal('0.12'))

        cpc_constraints.enforce_rule(max_cpc=Decimal('0.10'), ad_group_id=1, source_id=1)

        settings = models.AdGroupSource.objects.get(
            ad_group_id=1,
            source_id=1
        ).get_current_settings()
        self.assertEqual(settings.cpc_cc, Decimal('0.10'))
        settings = models.AdGroupSource.objects.get(
            ad_group_id=4,
            source_id=1
        ).get_current_settings()
        self.assertEqual(settings.cpc_cc, Decimal('0.12'))

    def test_clear(self):
        with self.assertRaises(AssertionError):
            cpc_constraints.clear(constants.CpcConstraintType.OUTBRAIN_BLACKLIST)

        models.CpcConstraint.objects.create(
            constraint_type=constants.CpcConstraintType.OUTBRAIN_BLACKLIST,
            min_cpc=Decimal('0.05'), agency_id=1)
        cpc_constraints.clear(constants.CpcConstraintType.OUTBRAIN_BLACKLIST, agency_id=1)
        self.assertFalse(models.CpcConstraint.objects.filter(
            agency_id=1,
            constraint_type=constants.CpcConstraintType.OUTBRAIN_BLACKLIST,
            min_cpc=Decimal('0.05')
        ))

        models.CpcConstraint.objects.create(
            constraint_type=constants.CpcConstraintType.MANUAL,
            min_cpc=Decimal('0.05'), account_id=1)
        cpc_constraints.clear(constants.CpcConstraintType.MANUAL, source_id=1)
        self.assertTrue(models.CpcConstraint.objects.filter(
            account_id=1,
            constraint_type=constants.CpcConstraintType.MANUAL,
            min_cpc=Decimal('0.05')
        ))
        cpc_constraints.clear(constants.CpcConstraintType.MANUAL, account_id=1)
        self.assertFalse(models.CpcConstraint.objects.filter(
            account_id=1,
            constraint_type=constants.CpcConstraintType.MANUAL,
            min_cpc=Decimal('0.05')
        ))


class AdjustCpcTestCase(test.TestCase):
    fixtures = ['test_models.yaml']

    def test_adjust_cpc_min_only(self):
        cpc_constraints.create(
            min_cpc=Decimal('0.05'),
            source_id=1,
            ad_group_id=1,
        )
        cpc = cpc_constraints.adjust_cpc(
            Decimal('0.01'),
            source=models.Source.objects.get(pk=1),
            ad_group=models.AdGroup.objects.get(pk=1),
        )
        self.assertEqual(cpc, Decimal('0.05'))

        cpc = cpc_constraints.adjust_cpc(
            Decimal('0.60'),
            source=models.Source.objects.get(pk=1),
            ad_group=models.AdGroup.objects.get(pk=1),
        )
        self.assertEqual(cpc, Decimal('0.60'))

    def test_adjust_cpc_max_only(self):
        cpc_constraints.create(
            max_cpc=Decimal('0.55'),
            source_id=1,
            ad_group_id=1,
        )
        cpc = cpc_constraints.adjust_cpc(
            Decimal('0.50'),
            source=models.Source.objects.get(pk=1),
            ad_group=models.AdGroup.objects.get(pk=1),
        )
        self.assertEqual(cpc, Decimal('0.50'))

        cpc = cpc_constraints.adjust_cpc(
            Decimal('0.60'),
            source=models.Source.objects.get(pk=1),
            ad_group=models.AdGroup.objects.get(pk=1),
        )
        self.assertEqual(cpc, Decimal('0.55'))

    def test_adjust_cpc_min_and_max(self):
        cpc_constraints.create(
            min_cpc=Decimal('0.05'),
            max_cpc=Decimal('0.15'),
            source_id=1,
            ad_group_id=1,
        )
        cpc = cpc_constraints.adjust_cpc(
            Decimal('0.01'),
            source=models.Source.objects.get(pk=1),
            ad_group=models.AdGroup.objects.get(pk=1),
        )
        self.assertEqual(cpc, Decimal('0.05'))
        cpc = cpc_constraints.adjust_cpc(
            Decimal('0.10'),
            source=models.Source.objects.get(pk=1),
            ad_group=models.AdGroup.objects.get(pk=1),
        )
        self.assertEqual(cpc, Decimal('0.10'))
        cpc = cpc_constraints.adjust_cpc(
            Decimal('0.20'),
            source=models.Source.objects.get(pk=1),
            ad_group=models.AdGroup.objects.get(pk=1),
        )
        self.assertEqual(cpc, Decimal('0.15'))

    def test_adjust_cpc_min_and_max_with_bcm_modifiers(self):
        cpc_constraints.create(
            min_cpc=Decimal('0.05'),
            max_cpc=Decimal('0.15'),
            source_id=1,
            ad_group_id=1,
        )
        bcm_modifiers = {
            'fee': Decimal('0.15'),
            'margin': Decimal('0.3'),
        }
        cpc = cpc_constraints.adjust_cpc(
            Decimal('0.01'),
            bcm_modifiers,
            source=models.Source.objects.get(pk=1),
            ad_group=models.AdGroup.objects.get(pk=1),
        )
        self.assertEqual(cpc, Decimal('0.09'))
        cpc = cpc_constraints.adjust_cpc(
            Decimal('0.10'),
            bcm_modifiers,
            source=models.Source.objects.get(pk=1),
            ad_group=models.AdGroup.objects.get(pk=1),
        )
        self.assertEqual(cpc, Decimal('0.10'))
        cpc = cpc_constraints.adjust_cpc(
            Decimal('0.30'),
            bcm_modifiers,
            source=models.Source.objects.get(pk=1),
            ad_group=models.AdGroup.objects.get(pk=1),
        )
        self.assertEqual(cpc, Decimal('0.25'))


class ValidateCpcTestCase(test.TestCase):
    fixtures = ['test_models.yaml']

    def test_validate_cpc(self):
        cpc_constraints.create(
            min_cpc=Decimal('0.05'),
            source_id=1,
            ad_group_id=1,
        )
        with self.assertRaises(forms.ValidationError) as err1:
            cpc_constraints.validate_cpc(
                Decimal('0.01'),
                source=models.Source.objects.get(pk=1),
                ad_group=models.AdGroup.objects.get(pk=1),
            )
        self.assertEqual(err1.exception.messages[0],
                         'Bid CPC is violating some constraints: '
                         'CPC constraint on source AdBlade with min. CPC $0.05')

        cpc_constraints.validate_cpc(
            Decimal('0.01'),
            source=models.Source.objects.get(pk=2),
            ad_group=models.AdGroup.objects.get(pk=1),
        )

    def test_validate_min_max_cpc_with_bcm_modifiers(self):
        cpc_constraints.create(
            min_cpc=Decimal('0.05'),
            max_cpc=Decimal('0.15'),
            source_id=1,
            ad_group_id=1,
        )
        bcm_modifiers = {
            'fee': Decimal('0.15'),
            'margin': Decimal('0.3'),
        }
        with self.assertRaises(forms.ValidationError) as err1:
            cpc_constraints.validate_cpc(
                Decimal('0.01'),
                bcm_modifiers,
                source=models.Source.objects.get(pk=1),
                ad_group=models.AdGroup.objects.get(pk=1),
            )
        self.assertEqual(err1.exception.messages[0],
                         'Bid CPC is violating some constraints: '
                         'CPC constraint on source AdBlade with '
                         'min. CPC $0.09 and max. CPC $0.25')

        with self.assertRaises(forms.ValidationError) as err2:
            cpc_constraints.validate_cpc(
                Decimal('0.30'),
                bcm_modifiers,
                source=models.Source.objects.get(pk=1),
                ad_group=models.AdGroup.objects.get(pk=1),
            )
        self.assertEqual(err2.exception.messages[0],
                         'Bid CPC is violating some constraints: '
                         'CPC constraint on source AdBlade with '
                         'min. CPC $0.09 and max. CPC $0.25')
        cpc_constraints.validate_cpc(
            Decimal('0.09'),
            bcm_modifiers,
            source=models.Source.objects.get(pk=1),
            ad_group=models.AdGroup.objects.get(pk=1),
        )
        cpc_constraints.validate_cpc(
            Decimal('0.25'),
            bcm_modifiers,
            source=models.Source.objects.get(pk=1),
            ad_group=models.AdGroup.objects.get(pk=1),
        )

    def test_validate_cpc_multiple(self):
        cpc_constraints.create(
            min_cpc=Decimal('0.05'),
            source_id=1,
            ad_group_id=1,
        )
        cpc_constraints.create(
            min_cpc=Decimal('0.02'),
            source_id=1,
            campaign_id=1,
        )
        with self.assertRaises(forms.ValidationError) as err1:
            cpc_constraints.validate_cpc(
                Decimal('0.01'),
                source=models.Source.objects.get(pk=1),
                ad_group=models.AdGroup.objects.get(pk=1),
            )
        self.assertEqual(err1.exception.messages[0],
                         'Bid CPC is violating some constraints: '
                         'CPC constraint on source AdBlade with min. CPC $0.05, '
                         'CPC constraint on source AdBlade with min. CPC $0.02')

    def test_validate_cpc_agency(self):
        class Request:
            pass
        req = Request()
        req.user = User.objects.get(pk=1)

        agency = models.Agency(
            name='Test Agency',
        )
        agency.save(req)
        account = models.Account.objects.get(pk=1)
        account.agency = agency
        account.save(req)
        cpc_constraints.create(
            min_cpc=Decimal('0.05'),
            source_id=1,
            agency=agency,
        )
        cpc_constraints.create(
            max_cpc=Decimal('0.50'),
            source_id=1,
            account=account,
        )
        with self.assertRaises(forms.ValidationError):
            cpc_constraints.validate_cpc(
                Decimal('0.01'),
                source=models.Source.objects.get(pk=1),
                account=models.Account.objects.get(pk=1),
            )
        with self.assertRaises(forms.ValidationError):
            cpc_constraints.validate_cpc(
                Decimal('0.01'),
                source=models.Source.objects.get(pk=1),
                campaign=models.Campaign.objects.get(pk=1),
            )
        with self.assertRaises(forms.ValidationError):
            cpc_constraints.validate_cpc(
                Decimal('0.01'),
                source=models.Source.objects.get(pk=1),
                ad_group=models.AdGroup.objects.get(pk=1),
            )
        with self.assertRaises(forms.ValidationError):
            cpc_constraints.validate_cpc(
                Decimal('0.01'),
                source=models.Source.objects.get(pk=1),
                agency=agency,
            )
        with self.assertRaises(forms.ValidationError):
            cpc_constraints.validate_cpc(
                Decimal('0.51'),
                source=models.Source.objects.get(pk=1),
                account=account,
            )
        with self.assertRaises(forms.ValidationError):
            cpc_constraints.validate_cpc(
                Decimal('0.51'),
                source=models.Source.objects.get(pk=1),
                campaign=models.Campaign.objects.get(pk=1),
            )
        with self.assertRaises(forms.ValidationError):
            cpc_constraints.validate_cpc(
                Decimal('0.51'),
                source=models.Source.objects.get(pk=1),
                ad_group=models.AdGroup.objects.get(pk=1),
            )
