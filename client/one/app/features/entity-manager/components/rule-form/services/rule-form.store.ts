import {Store} from 'rxjs-observable-store';
import {RuleFormStoreState} from './rule-form.store.state';
import {
    RuleDimension,
    TimeRange,
    RuleActionType,
    RuleConditionOperandType,
} from '../rule-form.constants';
import {RuleNotification} from '../types/rule-notification';
import {RuleCondition} from '../types/rule-condition';
import {RuleAction} from '../types/rule-action';
import {RuleActionConfig} from '../types/rule-action-config';
import {
    RULE_ACTIONS_OPTIONS,
    RULE_CONDITIONS_OPTIONS,
} from '../rule-form.config';
import {RuleConditionConfig} from '../types/rule-condition-config';

export class RuleFormStore extends Store<RuleFormStoreState> {
    constructor() {
        super(new RuleFormStoreState());
    }

    setRuleName(name: string) {
        this.updateState(name, 'rule', 'name');
    }

    selectRuleDimension(dimension: RuleDimension) {
        this.setState({
            ...this.state,
            availableActions: this.getActionsForDimension(dimension),
            availableConditions: this.getConditionsForDimension(dimension),
            rule: {
                ...this.state.rule,
                dimension: dimension,
                action: {type: null, frequency: null},
                conditions: [],
            },
        });
    }

    setRuleAction(action: RuleAction) {
        this.updateState(action, 'rule', 'action');
    }

    setNotification(notification: RuleNotification) {
        this.updateState(notification, 'rule', 'notification');
    }

    updateConditions(conditions: RuleCondition[]) {
        this.updateState(conditions, 'rule', 'conditions');
    }

    setRuleTimeRange(timeRange: TimeRange) {
        this.updateState(timeRange, 'rule', 'timeRange');
    }

    setRuleNotification(notification: RuleNotification) {
        this.updateState(notification, 'rule', 'notification');
    }

    private getActionsForDimension(
        dimension: RuleDimension
    ): RuleActionConfig[] {
        if (RuleDimension.Ad === dimension) {
            return [
                RULE_ACTIONS_OPTIONS[RuleActionType.IncreaseBidModifier],
                RULE_ACTIONS_OPTIONS[RuleActionType.DecreaseBidModifier],
                RULE_ACTIONS_OPTIONS[RuleActionType.TurnOff],
                RULE_ACTIONS_OPTIONS[RuleActionType.SendEmail],
            ];
        }
        if (RuleDimension.AdGroup === dimension) {
            return [
                RULE_ACTIONS_OPTIONS[RuleActionType.IncreaseCpc],
                RULE_ACTIONS_OPTIONS[RuleActionType.DecreaseCpc],
                RULE_ACTIONS_OPTIONS[RuleActionType.IncreaseCpm],
                RULE_ACTIONS_OPTIONS[RuleActionType.DecreaseCpm],
                RULE_ACTIONS_OPTIONS[RuleActionType.IncreaseDailyBudget],
                RULE_ACTIONS_OPTIONS[RuleActionType.DecreaseDailyBudget],
                RULE_ACTIONS_OPTIONS[RuleActionType.TurnOff],
                RULE_ACTIONS_OPTIONS[RuleActionType.SendEmail],
            ];
        }
        if (
            RuleDimension.AdGroupPublisher === dimension ||
            RuleDimension.AdGroupSource === dimension
        ) {
            return [
                RULE_ACTIONS_OPTIONS[RuleActionType.IncreaseBidModifier],
                RULE_ACTIONS_OPTIONS[RuleActionType.DecreaseBidModifier],
                RULE_ACTIONS_OPTIONS[RuleActionType.TurnOff],
                RULE_ACTIONS_OPTIONS[RuleActionType.SendEmail],
            ];
        }
        if (
            RuleDimension.AdGroupDevice === dimension ||
            RuleDimension.AdGroupCountry === dimension ||
            RuleDimension.AdGroupRegion === dimension ||
            RuleDimension.AdGroupDma === dimension ||
            RuleDimension.AdGroupOs === dimension ||
            RuleDimension.AdGroupPlacement === dimension
        ) {
            return [
                RULE_ACTIONS_OPTIONS[RuleActionType.IncreaseBidModifier],
                RULE_ACTIONS_OPTIONS[RuleActionType.DecreaseBidModifier],
                RULE_ACTIONS_OPTIONS[RuleActionType.SendEmail],
            ];
        }
        return [];
    }

    private getConditionsForDimension(
        dimension: RuleDimension
    ): RuleConditionConfig[] {
        // TODO (automation-rules): Return filtered list of conditions based on dimension
        return [
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.TotalSpend],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.Impressions],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.Clicks],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.Ctr],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.Cpc],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.Cpm],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.Visits],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.UniqueUsers],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.NewUsers],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.ReturningUsers],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.PercentNewUsers],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.ClickDiscrepancy],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.Pageviews],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.PageviewsPerVisit],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.BouncedVisits],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.NonBouncedVisits],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.BounceRate],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.TotalSeconds],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.TimeOnSite],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.RemainingCampaignBudget
            ],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.CampaignBudgetMargin
            ],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.CampaignBudgetStartDate
            ],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.CampaignBudgetEndDate
            ],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.DaysSinceCampaignBudgetStart
            ],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.DaysUntilCampaignBudgetEnd
            ],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.AccountName],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.AccountCreationDate
            ],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.DaysSinceAccountCreation
            ],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.CampaignName],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.CampaignCreationDate
            ],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.DaysSinceCampaignCreation
            ],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.CampaignManager],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.AdGroupName],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.AdGroupCreationDate
            ],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.DaysSinceAdGroupCreation
            ],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.AdGroupStartDate],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.AdGroupEndDate],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.AdGroupDailyBudget
            ],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.CreativeName],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.CreativeLabel],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.CreativeCreationDate
            ],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.DaysSinceCreativeCreation
            ],
        ];
    }
}
