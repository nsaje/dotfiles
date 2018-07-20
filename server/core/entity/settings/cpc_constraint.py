# -*- coding: utf-8 -*-

from django.db import models

from dash import constants
from utils import lc_helper

import core.bcm
import core.common
import core.entity
import core.source


class CpcConstraint(models.Model):
    class Meta:
        app_label = "dash"

    id = models.AutoField(primary_key=True)
    min_cpc = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, verbose_name="Minimum CPC")
    max_cpc = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, verbose_name="Maximum CPC")
    agency = models.ForeignKey(
        core.entity.Agency, null=True, blank=True, related_name="cpc_constraints", on_delete=models.PROTECT
    )
    account = models.ForeignKey(
        core.entity.Account, null=True, blank=True, related_name="cpc_constraints", on_delete=models.PROTECT
    )
    campaign = models.ForeignKey(
        core.entity.Campaign, null=True, blank=True, related_name="cpc_constraints", on_delete=models.PROTECT
    )
    ad_group = models.ForeignKey(
        core.entity.AdGroup, null=True, blank=True, related_name="cpc_constraints", on_delete=models.PROTECT
    )
    source = models.ForeignKey(
        core.source.Source, null=True, blank=True, related_name="cpc_constraints", on_delete=models.PROTECT
    )
    constraint_type = models.IntegerField(
        default=constants.CpcConstraintType.MANUAL, choices=constants.CpcConstraintType.get_choices()
    )
    reason = models.TextField(null=True, blank=True)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")

    objects = core.common.QuerySetManager()

    def __str__(self):
        desc = "CPC constraint"
        if self.source:
            desc += " on source {}".format(self.source.name)
        else:
            desc += " on all sources"
        desc += " with"

        if hasattr(self, "bcm_min_cpc") and self.bcm_min_cpc:
            desc += " min. CPC {}".format(lc_helper.default_currency(self.bcm_min_cpc))
        if hasattr(self, "bcm_max_cpc") and self.bcm_max_cpc:
            if hasattr(self, "bcm_min_cpc") and self.bcm_min_cpc:
                desc += " and"
            desc += " max. CPC {}".format(lc_helper.default_currency(self.bcm_max_cpc))
        return desc

    class QuerySet(models.QuerySet):
        def filter_applied(self, cpc, bcm_modifiers, source=None, **levels):
            ad_group = levels.get("ad_group")
            campaign, account, agency = core.entity.helpers.generate_parents(**levels)
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
                bcm_min_cpc=CpcConstraint.QuerySet._transform_min_cpc_to_bcm(bcm_modifiers),
                bcm_max_cpc=CpcConstraint.QuerySet._transform_max_cpc_to_bcm(bcm_modifiers),
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
            return CpcConstraint.QuerySet._round_ceil(CpcConstraint.QuerySet._apply_bcm_modifiers(field, bcm_modifiers))

        @staticmethod
        def _transform_max_cpc_to_bcm(bcm_modifiers):
            field = models.F("max_cpc")
            if not bcm_modifiers:
                return field
            return CpcConstraint.QuerySet._round_floor(
                CpcConstraint.QuerySet._apply_bcm_modifiers(field, bcm_modifiers)
            )

        @staticmethod
        def _apply_bcm_modifiers(field, bcm_modifiers):
            return core.bcm.calculations.apply_fee_and_margin(field, bcm_modifiers["fee"], bcm_modifiers["margin"])

        @staticmethod
        def _round_ceil(field):
            return CpcConstraint.QuerySet._round(models.Func(field * 100, function="CEIL") / 100)

        @staticmethod
        def _round_floor(field):
            return CpcConstraint.QuerySet._round(models.Func(field * 100, function="FLOOR") / 100)

        @staticmethod
        def _round(field):
            return models.Func(field, 2, function="ROUND")
