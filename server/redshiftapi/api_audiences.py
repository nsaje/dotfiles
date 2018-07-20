import datetime

import backtosql
from dash import constants
from . import db


def get_audience_sample_size(account_id, slug, ttl, rules, refresh_cache=False):
    timelimit = datetime.datetime.now().date() - datetime.timedelta(days=ttl)

    valid_rule_types = [
        constants.AudienceRuleType.STARTS_WITH,
        constants.AudienceRuleType.CONTAINS,
        constants.AudienceRuleType.NOT_STARTS_WITH,
        constants.AudienceRuleType.NOT_CONTAINS,
    ]

    query_rules = []
    params = [account_id, slug, timelimit.isoformat()]
    if not any(rule.type == constants.AudienceRuleType.VISIT for rule in rules):
        for rule in rules:
            if rule.type not in valid_rule_types:
                raise Exception("Unknown rule: %s".format(rule.type))

            values = rule.value.split(",")
            for val in values:
                val = val.strip()
                params.append(val)

            query_rules.append({"type": rule.type, "values": values})

    result = db.execute_query(
        backtosql.generate_sql(
            "audience_sample_size.sql", {"rules": query_rules, "rule_type": constants.AudienceRuleType}
        ),
        params,
        "audience_sample_size",
        cache_name="audience_sample_size",
        refresh_cache=refresh_cache,
    )
    return result[0]["count"]
