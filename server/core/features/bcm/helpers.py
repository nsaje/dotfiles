from django.core.exceptions import ValidationError
from django.db.models import Func
from django.forms.models import model_to_dict

import core.features.bcm
import core.features.bcm.bcm_slack
import core.features.multicurrency
import dash.constants
import utils.slack


class Round(Func):
    function = "ROUND"
    template = "%(function)s(%(expressions)s, 0)"


class Coalesce(Func):
    function = "COALESCE"
    template = "%(function)s(%(expressions)s, 0)"


def validate(*validators):
    errors = {}
    for v in validators:
        try:
            v()
        except ValidationError as e:
            errors[v.__name__.replace("validate_", "")] = e.error_list
    if errors:
        raise ValidationError(errors)


def notify_credit_to_slack(credit, action_type=None):
    if action_type == dash.constants.HistoryActionType.CREATE:
        if credit.account is not None:
            if not (credit.contract_id or credit.contract_number):
                core.features.bcm.bcm_slack.log_to_slack(
                    credit.account_id,
                    core.features.bcm.bcm_slack.SLACK_NEW_CREDIT_WITHOUT_CONTRACT_MSG.format(
                        credit_id=credit.pk,
                        # TODO (msuber): change url when MC credits library is in production
                        # url=core.features.bcm.bcm_slack.ACCOUNT_URL.format(
                        #     agency_id=credit.account.agency_id,
                        #     account_id=credit.account_id
                        # ),
                        url=core.features.bcm.bcm_slack.ACCOUNT_URL.format(credit.account_id),
                        account_name=credit.account.get_long_name(),
                        amount=credit.amount,
                        currency_symbol=core.features.multicurrency.get_currency_symbol(credit.currency),
                        end_date=credit.end_date,
                        comment="Comments: _{}_".format(credit.comment) if credit.comment else "",
                    ),
                    msg_type=utils.slack.MESSAGE_TYPE_WARNING,
                )
                return
            core.features.bcm.bcm_slack.log_to_slack(
                credit.account_id,
                core.features.bcm.bcm_slack.SLACK_NEW_CREDIT_MSG.format(
                    credit_id=credit.pk,
                    # TODO (msuber): change url when MC credits library is in production
                    # url=core.features.bcm.bcm_slack.ACCOUNT_URL.format(
                    #     agency_id=credit.account.agency_id,
                    #     account_id=credit.account_id
                    # ),
                    url=core.features.bcm.bcm_slack.ACCOUNT_URL.format(credit.account_id),
                    account_name=credit.account.get_long_name(),
                    amount=credit.amount,
                    currency_symbol=core.features.multicurrency.get_currency_symbol(credit.currency),
                    end_date=credit.end_date,
                ),
            )
        elif credit.agency is not None:
            if not (credit.contract_id or credit.contract_number):
                core.features.bcm.bcm_slack.log_to_slack(
                    None,
                    core.features.bcm.bcm_slack.SLACK_NEW_AGENCY_CREDIT_WITHOUT_CONTRACT_MSG.format(
                        credit_id=credit.pk,
                        # TODO (msuber): change url when MC credits library is in production
                        # url=core.features.bcm.bcm_slack.AGENCY_URL.format(agency_id=credit.agency_id),
                        agency_name=credit.agency.name,
                        amount=credit.amount,
                        currency_symbol=core.features.multicurrency.get_currency_symbol(credit.currency),
                        end_date=credit.end_date,
                        comment="Comments: _{}_".format(credit.comment) if credit.comment else "",
                    ),
                    msg_type=utils.slack.MESSAGE_TYPE_WARNING,
                )
                return
            core.features.bcm.bcm_slack.log_to_slack(
                None,
                core.features.bcm.bcm_slack.SLACK_NEW_AGENCY_CREDIT_MSG.format(
                    credit_id=credit.pk,
                    # TODO (msuber): change url when MC credits library is in production
                    # url=core.features.bcm.bcm_slack.AGENCY_URL.format(agency_id=credit.agency_id),
                    agency_name=credit.agency.name,
                    amount=credit.amount,
                    currency_symbol=core.features.multicurrency.get_currency_symbol(credit.currency),
                    end_date=credit.end_date,
                ),
            )
    elif action_type == dash.constants.HistoryActionType.CREDIT_CHANGE:
        changes = credit.get_model_state_changes(model_to_dict(credit))
        if credit.account is not None:
            core.features.bcm.bcm_slack.log_to_slack(
                credit.account_id,
                core.features.bcm.bcm_slack.SLACK_UPDATED_CREDIT_MSG.format(
                    credit_id=credit.id,
                    # TODO (msuber): change url when MC credits library is in production
                    # url=core.features.bcm.bcm_slack.ACCOUNT_URL.format(
                    #     agency_id=credit.account.agency_id,
                    #     account_id=credit.account_id
                    # ),
                    url=core.features.bcm.bcm_slack.ACCOUNT_URL.format(credit.account_id),
                    account_name=credit.account.get_long_name(),
                    history=credit.get_history_changes_text(changes),
                ),
            )
        elif credit.agency is not None:
            core.features.bcm.bcm_slack.log_to_slack(
                None,
                core.features.bcm.bcm_slack.SLACK_UPDATED_AGENCY_CREDIT_MSG.format(
                    credit_id=credit.id,
                    # TODO (msuber): change url when MC credits library is in production
                    # url=core.features.bcm.bcm_slack.AGENCY_URL.format(agency_id=credit.agency_id),
                    agency_name=credit.agency.name,
                    history=credit.get_history_changes_text(changes),
                ),
            )


def notify_budget_to_slack(budget, action_type=None):
    if action_type == dash.constants.HistoryActionType.CREATE:
        core.features.bcm.bcm_slack.log_to_slack(
            budget.campaign.account_id,
            core.features.bcm.bcm_slack.SLACK_NEW_BUDGET_MSG.format(
                budget_id=budget.id,
                url=core.features.bcm.bcm_slack.CAMPAIGN_URL.format(campaign_id=budget.campaign_id),
                campaign_name=budget.campaign.get_long_name(),
                amount=budget.amount,
                margin=budget.margin * 100,
                currency_symbol=core.features.multicurrency.get_currency_symbol(budget.credit.currency),
                end_date=budget.end_date,
            ),
        )
    elif action_type == dash.constants.HistoryActionType.BUDGET_CHANGE:
        changes = budget.get_model_state_changes(model_to_dict(budget))
        core.features.bcm.bcm_slack.log_to_slack(
            budget.campaign.account_id,
            core.features.bcm.bcm_slack.SLACK_UPDATED_BUDGET_MSG.format(
                budget_id=budget.id,
                url=core.features.bcm.bcm_slack.CAMPAIGN_URL.format(campaign_id=budget.campaign_id),
                campaign_name=budget.campaign.get_long_name(),
                history=budget.get_history_changes_text(changes),
            ),
        )
