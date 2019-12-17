import {Store} from 'rxjs-observable-store';
import {RuleEditFormStoreState} from './rule-edit-form.store.state';
import {
    RuleTargetType,
    TimeRange,
    RuleActionType,
    RuleConditionOperandType,
    RuleNotificationType,
    RuleActionFrequency,
} from '../../../../../core/rules/rules.constants';
import {RuleCondition} from '../../../../../core/rules/types/rule-condition';
import {RuleActionConfig} from '../../../../../core/rules/types/rule-action-config';
import {
    RULE_ACTIONS_OPTIONS,
    RULE_CONDITIONS_OPTIONS,
} from '../../../rules-library.config';
import {RulesService} from '../../../../../core/rules/services/rules.service';
import {RuleConditionConfig} from '../../../../../core/rules/types/rule-condition-config';
import * as storeHelpers from '../../../../../shared/helpers/store.helpers';
import {RequestStateUpdater} from '../../../../../shared/types/request-state-updater';
import {Injectable, OnDestroy} from '@angular/core';
import {takeUntil} from 'rxjs/operators';
import {Subject} from 'rxjs';
import {ChangeEvent} from '../../../../../shared/types/change-event';

@Injectable()
export class RuleEditFormStore extends Store<RuleEditFormStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<void> = new Subject();
    private requestStateUpdater: RequestStateUpdater;

    constructor(private rulesService: RulesService) {
        super(new RuleEditFormStoreState());
        this.requestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this
        );
    }

    initStore(agencyId: string, adGroupId: string) {
        this.setState({
            ...this.state,
            agencyId: agencyId,
            rule: {
                ...this.state.rule,
                entities: {
                    ...this.state.rule.entities,
                    adGroup: {
                        ...this.state.rule.entities.adGroup,
                        included: [adGroupId],
                    },
                },
            },
        });
    }

    saveEntity(): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.rulesService
                .save(
                    this.state.agencyId,
                    this.state.rule,
                    this.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    () => {
                        resolve();
                    },
                    error => {
                        reject();
                    }
                );
        });
    }

    setRuleName(name: string) {
        this.patchState(name, 'rule', 'name');
    }

    selectRuleTarget(target: RuleTargetType) {
        this.setState({
            ...this.state,
            availableActions: this.getActionsForTarget(target),
            availableConditions: this.getConditionsForTarget(target),
            rule: {
                ...this.state.rule,
                targetType: target,
                actionType: null,
                actionFrequency: null,
                conditions: [],
            },
        });
    }

    setRuleActionType(actionType: RuleActionType) {
        if (!actionType) {
            this.setState({
                ...this.state,
                rule: {
                    ...this.state.rule,
                    actionType: actionType,
                    actionFrequency: null,
                },
            });
        } else {
            this.patchState(actionType, 'rule', 'actionType');
        }
    }

    setRuleActionFrequency(actionFrequency: RuleActionFrequency) {
        this.patchState(actionFrequency, 'rule', 'actionFrequency');
    }

    setRuleChangeStep(changeStep: number) {
        this.patchState(changeStep, 'rule', 'changeStep');
    }

    setRuleChangeLimit(changeLimit: number) {
        this.patchState(changeLimit, 'rule', 'changeLimit');
    }

    addCondition(condition: RuleCondition) {
        this.setState({
            ...this.state,
            rule: {
                ...this.state.rule,
                conditions: [...this.state.rule.conditions, condition],
            },
        });
    }

    updateCondition(conditionChange: ChangeEvent<RuleCondition>) {
        const newConditions = this.state.rule.conditions.map(condition => {
            if (condition === conditionChange.target) {
                return {
                    ...condition,
                    ...conditionChange.changes,
                };
            }
            return condition;
        });
        this.setState({
            ...this.state,
            rule: {
                ...this.state.rule,
                conditions: newConditions,
            },
        });
    }

    removeCondition(removedCondition: RuleCondition) {
        const newConditions = this.state.rule.conditions.filter(condition => {
            return condition !== removedCondition;
        });
        this.setState({
            ...this.state,
            rule: {
                ...this.state.rule,
                conditions: newConditions,
            },
        });
    }

    setRuleTimeRange(timeRange: TimeRange) {
        this.patchState(timeRange, 'rule', 'window');
    }

    setRuleNotificationType(notificationType: RuleNotificationType) {
        this.patchState(notificationType, 'rule', 'notificationType');
    }

    setRuleNotificationRecipients(notificationRecipients: string[]) {
        this.patchState(
            notificationRecipients,
            'rule',
            'notificationRecipients'
        );
    }

    private getActionsForTarget(target: RuleTargetType): RuleActionConfig[] {
        if (RuleTargetType.Ad === target) {
            return [
                RULE_ACTIONS_OPTIONS[RuleActionType.IncreaseBidModifier],
                RULE_ACTIONS_OPTIONS[RuleActionType.DecreaseBidModifier],
                RULE_ACTIONS_OPTIONS[RuleActionType.TurnOff],
            ];
        }
        if (RuleTargetType.AdGroup === target) {
            return [
                RULE_ACTIONS_OPTIONS[RuleActionType.IncreaseBid],
                RULE_ACTIONS_OPTIONS[RuleActionType.DecreaseBid],
                RULE_ACTIONS_OPTIONS[RuleActionType.IncreaseDailyBudget],
                RULE_ACTIONS_OPTIONS[RuleActionType.DecreaseDailyBudget],
                RULE_ACTIONS_OPTIONS[RuleActionType.TurnOff],
            ];
        }
        if (RuleTargetType.AdGroupPublisher === target) {
            return [
                RULE_ACTIONS_OPTIONS[RuleActionType.IncreaseBidModifier],
                RULE_ACTIONS_OPTIONS[RuleActionType.DecreaseBidModifier],
                // RULE_ACTIONS_OPTIONS[RuleActionType.Blacklist],
            ];
        }
        if (RuleTargetType.AdGroupSource === target) {
            return [
                RULE_ACTIONS_OPTIONS[RuleActionType.IncreaseBidModifier],
                RULE_ACTIONS_OPTIONS[RuleActionType.DecreaseBidModifier],
                RULE_ACTIONS_OPTIONS[RuleActionType.TurnOff],
            ];
        }
        if (
            RuleTargetType.AdGroupDevice === target ||
            RuleTargetType.AdGroupCountry === target ||
            RuleTargetType.AdGroupRegion === target ||
            RuleTargetType.AdGroupDma === target ||
            RuleTargetType.AdGroupOs === target ||
            RuleTargetType.AdGroupPlacement === target
        ) {
            return [
                RULE_ACTIONS_OPTIONS[RuleActionType.IncreaseBidModifier],
                RULE_ACTIONS_OPTIONS[RuleActionType.DecreaseBidModifier],
            ];
        }
        return [];
    }

    private getConditionsForTarget(
        target: RuleTargetType
    ): RuleConditionConfig[] {
        // TODO (automation-rules): Return filtered list of conditions based on target
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
            // RULE_CONDITIONS_OPTIONS[
            //     RuleConditionOperandType.RemainingCampaignBudget
            // ],
            // RULE_CONDITIONS_OPTIONS[
            //     RuleConditionOperandType.CampaignBudgetMargin
            // ],
            // RULE_CONDITIONS_OPTIONS[
            //     RuleConditionOperandType.CampaignBudgetStartDate
            // ],
            // RULE_CONDITIONS_OPTIONS[
            //     RuleConditionOperandType.CampaignBudgetEndDate
            // ],
            // RULE_CONDITIONS_OPTIONS[
            //     RuleConditionOperandType.DaysSinceCampaignBudgetStart
            // ],
            // RULE_CONDITIONS_OPTIONS[
            //     RuleConditionOperandType.DaysUntilCampaignBudgetEnd
            // ],
            // RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.AccountName],
            // RULE_CONDITIONS_OPTIONS[
            //     RuleConditionOperandType.AccountCreationDate
            // ],
            // RULE_CONDITIONS_OPTIONS[
            //     RuleConditionOperandType.DaysSinceAccountCreation
            // ],
            // RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.CampaignName],
            // RULE_CONDITIONS_OPTIONS[
            //     RuleConditionOperandType.CampaignCreationDate
            // ],
            // RULE_CONDITIONS_OPTIONS[
            //     RuleConditionOperandType.DaysSinceCampaignCreation
            // ],
            // RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.CampaignManager],
            // RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.AdGroupName],
            // RULE_CONDITIONS_OPTIONS[
            //     RuleConditionOperandType.AdGroupCreationDate
            // ],
            // RULE_CONDITIONS_OPTIONS[
            //     RuleConditionOperandType.DaysSinceAdGroupCreation
            // ],
            // RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.AdGroupStartDate],
            // RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.AdGroupEndDate],
            // RULE_CONDITIONS_OPTIONS[
            //     RuleConditionOperandType.AdGroupDailyBudget
            // ],
            // RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.CreativeName],
            // RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.CreativeLabel],
            // RULE_CONDITIONS_OPTIONS[
            //     RuleConditionOperandType.CreativeCreationDate
            // ],
            // RULE_CONDITIONS_OPTIONS[
            //     RuleConditionOperandType.DaysSinceCreativeCreation
            // ],
        ];
    }

    ngOnDestroy() {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }
}
