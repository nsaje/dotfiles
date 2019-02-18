from django.db import models

import core.features.bcm
import core.models.helpers


class CpcConstraintQuerySet(models.QuerySet):
    def filter_applied(self, cpc, bcm_modifiers, source=None, **levels):
        ad_group = levels.get("ad_group")
        campaign, account, agency = core.models.helpers.generate_parents(**levels)
        rules = models.Q()
        if agency:
            rules |= models.Q(agency=agency)
        if account:
            rules |= models.Q(account=account)
        if campaign:
            rules |= models.Q(campaign=campaign)
        if ad_group:
            rules |= models.Q(ad_group=ad_group)

        queryset = self.filter(rules).annotate(
            bcm_min_cpc=self._transform_min_cpc_to_bcm(bcm_modifiers),
            bcm_max_cpc=self._transform_max_cpc_to_bcm(bcm_modifiers),
        )
        if cpc is not None:
            queryset = queryset.filter(
                models.Q(bcm_min_cpc__isnull=False) & models.Q(bcm_min_cpc__gt=cpc)
                | models.Q(bcm_max_cpc__isnull=False) & models.Q(bcm_max_cpc__lt=cpc)
            )

        if source:
            queryset = queryset.filter(models.Q(source=source) | models.Q(source=None))

        return queryset

    @staticmethod
    def _transform_min_cpc_to_bcm(bcm_modifiers):
        field = models.F("min_cpc")
        if not bcm_modifiers:
            return field
        return CpcConstraintQuerySet._round_ceil(CpcConstraintQuerySet._apply_bcm_modifiers(field, bcm_modifiers))

    @staticmethod
    def _transform_max_cpc_to_bcm(bcm_modifiers):
        field = models.F("max_cpc")
        if not bcm_modifiers:
            return field
        return CpcConstraintQuerySet._round_floor(CpcConstraintQuerySet._apply_bcm_modifiers(field, bcm_modifiers))

    @staticmethod
    def _apply_bcm_modifiers(field, bcm_modifiers):
        return core.features.bcm.calculations.apply_fee_and_margin(field, bcm_modifiers["fee"], bcm_modifiers["margin"])

    @staticmethod
    def _round_ceil(field):
        return CpcConstraintQuerySet._round(models.Func(field * 100, function="CEIL") / 100)

    @staticmethod
    def _round_floor(field):
        return CpcConstraintQuerySet._round(models.Func(field * 100, function="FLOOR") / 100)

    @staticmethod
    def _round(field):
        return models.Func(field, 2, function="ROUND")
