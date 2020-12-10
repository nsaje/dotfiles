import django.core.exceptions
from django.core import validators
from django.db import transaction

import core.common
import core.features.audiences
from dash import constants
from utils import k1_helper

from . import exceptions
from . import model


class AudienceManager(core.common.BaseManager):
    @transaction.atomic
    def create(self, request, name, pixel, ttl, prefill_days, rules):
        rules = self._clean_rules(rules)
        self._validate_pixel(pixel)
        self._validate_rule_values(rules)
        self._validate_rules(rules, pixel, ttl)

        audience = None

        with transaction.atomic():
            audience = model.Audience(
                name=name,
                pixel=pixel,
                ttl=ttl,
                prefill_days=ttl or prefill_days or 0,  # use ttl value for prefill until it gets its own UI component
                created_by=request.user,
            )

            audience._save()
            audience.add_to_history(
                request.user,
                constants.HistoryActionType.AUDIENCE_CREATE,
                'Created audience "{}".'.format(audience.name),
            )

            for rule in rules:
                rule = core.features.audiences.AudienceRule(
                    audience=audience, type=rule["type"], value=rule.get("value") or ""
                )
                rule.save()

        k1_helper.update_account(pixel.account, msg="audience.create")

        return audience

    def _validate_pixel(self, pixel):
        if pixel.archived:
            raise exceptions.PixelIsArchived("Pixel is archived.")

    def _clean_rules(self, rules):
        refererRules = (constants.AudienceRuleType.CONTAINS, constants.AudienceRuleType.STARTS_WITH)
        for rule in rules:
            value = rule.get("value") or ""
            if int(rule.get("type")) in refererRules:
                rule["value"] = ",".join([x.strip() for x in value.split(",") if x])
        return rules

    def _validate_rule_values(self, rules):
        for rule in rules:
            if not rule.get("value") and str(rule["type"]) != str(constants.AudienceRuleType.VISIT):
                raise exceptions.RuleValueMissing("Please enter conditions for the audience.")

            if str(rule["type"]) == str(constants.AudienceRuleType.STARTS_WITH):
                for url in rule["value"].split(","):
                    validate_url = validators.URLValidator(schemes=["http", "https"])
                    try:
                        validate_url(url)
                    except django.core.exceptions.ValidationError:
                        raise exceptions.RuleUrlInvalid("Please enter valid URLs.")

    def _validate_rules(self, rules, pixel, ttl):
        rule_rows = [(rule["type"], rule.get("value") or "") for rule in rules]
        audience_ids = core.features.audiences.Audience.objects.filter(pixel=pixel, ttl=ttl, archived=False).values(
            "id"
        )
        audience_ids = [a["id"] for a in audience_ids]

        for rule in core.features.audiences.AudienceRule.objects.filter(audience_id__in=audience_ids).values(
            "audience_id", "value", "type"
        ):
            row = (rule["type"], rule["value"])
            if row in rule_rows:
                existing_audience_names = core.features.audiences.Audience.objects.filter(
                    id=rule["audience_id"]
                ).values("name")
                if len(existing_audience_names) > 0:
                    raise exceptions.RuleTtlCombinationAlreadyExists(
                        "Audience {} with the same ttl and rule already exists.".format(
                            existing_audience_names[0]["name"]
                        )
                    )
