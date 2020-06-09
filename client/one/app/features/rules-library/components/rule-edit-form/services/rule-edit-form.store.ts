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
import {PublisherGroupsService} from '../../../../../core/publisher-groups/services/publisher-groups.service';
import {RulesService} from '../../../../../core/rules/services/rules.service';
import {RuleConditionConfig} from '../../../../../core/rules/types/rule-condition-config';
import * as storeHelpers from '../../../../../shared/helpers/store.helpers';
import {RequestStateUpdater} from '../../../../../shared/types/request-state-updater';
import {Injectable, OnDestroy} from '@angular/core';
import {takeUntil} from 'rxjs/operators';
import {Subject} from 'rxjs';
import {ChangeEvent} from '../../../../../shared/types/change-event';
import {HttpErrorResponse} from '@angular/common/http';
import {RulesEditFormStoreFieldsErrorsState} from './rule-edit-form.fields-errors-state';
import {PublisherGroup} from '../../../../../core/publisher-groups/types/publisher-group';
import * as commonHelpers from '../../../../../shared/helpers/common.helpers';

@Injectable()
export class RuleEditFormStore extends Store<RuleEditFormStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<void> = new Subject();
    private requestStateUpdater: RequestStateUpdater;
    private publisherGroupsRequestStateUpdater: RequestStateUpdater;

    constructor(
        private rulesService: RulesService,
        private publisherGroupsService: PublisherGroupsService
    ) {
        super(new RuleEditFormStoreState());
        this.requestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this
        );
        this.publisherGroupsRequestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this,
            'publisherGroupsRequests'
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
                    (error: HttpErrorResponse) => {
                        const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                            new RulesEditFormStoreFieldsErrorsState(),
                            error
                        );
                        this.patchState(fieldsErrors, 'fieldsErrors');
                        reject();
                    }
                );
        });
    }

    setRuleName(name: string) {
        this.patchState(name, 'rule', 'name');
    }

    setRuleTargetAction(targetActionType: {
        targetType: RuleTargetType;
        actionType: RuleActionType;
    }) {
        // reset fields that depend on action / target type
        const availableConditions = this.getConditionsForTarget(
            targetActionType.targetType
        );
        this.setState({
            ...this.state,
            availableConditions: availableConditions,
            rule: {
                ...this.state.rule,
                targetType: targetActionType.targetType,
                actionType: targetActionType.actionType,
                actionFrequency: null,
                changeStep: null,
                changeLimit: null,
                sendEmailRecipients: [],
                sendEmailSubject: null,
                sendEmailBody: null,
                publisherGroupId: null,
                conditions: this.filterConditionsValidForTarget(
                    availableConditions,
                    this.state.rule.conditions
                ),
            },
        });
    }

    filterConditionsValidForTarget(
        availableConditions: RuleConditionConfig[],
        conditions: RuleCondition[]
    ): RuleCondition[] {
        const availableConditionTypes = new Set();
        availableConditions.forEach(ruleConditionConfig => {
            availableConditionTypes.add(ruleConditionConfig.metric.type);
        });
        return conditions.filter(condition => {
            return availableConditionTypes.has(condition.metric.type);
        });
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

    setSendEmailRecipients(recipients: string) {
        let recipientsList: string[] = [];
        if (recipients.length > 0) {
            recipientsList = recipients.split(/[\s,]+/);
        }
        this.patchState(recipientsList, 'rule', 'sendEmailRecipients');
    }

    setSendEmailSubject(subject: string) {
        this.patchState(subject, 'rule', 'sendEmailSubject');
    }

    setSendEmailBody(body: string) {
        this.patchState(body, 'rule', 'sendEmailBody');
    }

    setPublisherGroupId(publisherGroupId: string) {
        this.patchState(publisherGroupId, 'rule', 'publisherGroupId');
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
        let notificationRecipients = this.state.rule.notificationRecipients;
        if (notificationType === RuleNotificationType.None) {
            notificationRecipients = [];
        }
        this.setState({
            ...this.state,
            rule: {
                ...this.state.rule,
                notificationType: notificationType,
                notificationRecipients: notificationRecipients,
            },
        });
    }

    setRuleNotificationRecipients(recipients: string) {
        let recipientsList: string[] = [];
        if (recipients.length > 0) {
            recipientsList = recipients.split(/[\s,]+/);
        }
        this.patchState(recipientsList, 'rule', 'notificationRecipients');
    }

    loadAvailablePublisherGroups(keyword: string | null) {
        return new Promise<void>((resolve, reject) => {
            const isKeywordDefined = commonHelpers.isDefined(keyword);
            this.publisherGroupsService
                .listExplicit(
                    this.state.agencyId,
                    null,
                    !isKeywordDefined ? null : keyword.trim(),
                    0,
                    10,
                    this.publisherGroupsRequestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (publisherGroups: PublisherGroup[]) => {
                        this.patchState(
                            publisherGroups,
                            'availablePublisherGroups'
                        );
                        resolve();
                    },
                    error => {
                        reject();
                    }
                );
        });
    }

    private getConditionsForTarget(
        target: RuleTargetType
    ): RuleConditionConfig[] {
        const conditions = [
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
                RuleConditionOperandType.AvgCostPerConversion
            ],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.AvgCostPerConversionView
            ],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.AvgCostPerConversionTotal
            ],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.AccountName],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.AccountCreatedDate
            ],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.DaysSinceAccountCreated
            ],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.CampaignName],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.CampaignCreatedDate
            ],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.DaysSinceCampaignCreated
            ],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.CampaignManager],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.AdGroupName],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.AdGroupCreatedDate
            ],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.DaysSinceAdGroupCreated
            ],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.AdGroupStartDate],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.AdGroupEndDate],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.AdGroupDailyCap],
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
        ];

        if (target === RuleTargetType.Ad) {
            conditions.push(
                RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.AdTitle],
                RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.AdLabel],
                RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.AdCreatedDate],
                RULE_CONDITIONS_OPTIONS[
                    RuleConditionOperandType.DaysSinceAdCreated
                ]
            );
        }
        return conditions;
    }

    ngOnDestroy() {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }
}
