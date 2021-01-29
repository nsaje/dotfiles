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
import {RULE_CONDITIONS_OPTIONS, ENTITY_TYPE_TEXT} from '../../../rules.config';
import {PublisherGroupsService} from '../../../../../core/publisher-groups/services/publisher-groups.service';
import {RulesService} from '../../../../../core/rules/services/rules.service';
import {RuleConditionConfig} from '../../../../../core/rules/types/rule-condition-config';
import * as storeHelpers from '../../../../../shared/helpers/store.helpers';
import {RequestStateUpdater} from '../../../../../shared/types/request-state-updater';
import {Injectable, OnDestroy, Inject} from '@angular/core';
import {takeUntil} from 'rxjs/operators';
import {Subject} from 'rxjs';
import {ChangeEvent} from '../../../../../shared/types/change-event';
import {HttpErrorResponse} from '@angular/common/http';
import {RulesEditFormStoreFieldsErrorsState} from './rule-edit-form.fields-errors-state';
import {PublisherGroup} from '../../../../../core/publisher-groups/types/publisher-group';
import * as commonHelpers from '../../../../../shared/helpers/common.helpers';
import {Rule} from '../../../../../core/rules/types/rule';
import {AccountService} from '../../../../../core/entities/services/account/account.service';
import {Account} from '../../../../../core/entities/types/account/account';
import {ScopeSelectorState} from '../../../../../shared/components/scope-selector/scope-selector.constants';
import {RuleEntity} from '../../../../../core/rules/types/rule-entity';
import {AdGroupService} from '../../../../../core/entities/services/ad-group/ad-group.service';
import {CampaignService} from '../../../../../core/entities/services/campaign/campaign.service';
import {AdGroup} from '../../../../../core/entities/types/ad-group/ad-group';
import {Campaign} from '../../../../../core/entities/types/campaign/campaign';
import * as clone from 'clone';
import {EntityType} from '../../../../../app.constants';
import {EntitySelectorItem} from '../../../../../shared/components/entity-selector/types/entity-selector-item';
import {AuthStore} from '../../../../../core/auth/services/auth.store';
import {ConversionPixelsService} from '../../../../../core/conversion-pixels/services/conversion-pixels.service';
import {ConversionPixel} from '../../../../../core/conversion-pixels/types/conversion-pixel';

@Injectable()
export class RuleEditFormStore extends Store<RuleEditFormStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<void> = new Subject();
    private requestStateUpdater: RequestStateUpdater;
    private publisherGroupsRequestStateUpdater: RequestStateUpdater;
    private accountsRequestStateUpdater: RequestStateUpdater;
    private campaignsRequestStateUpdater: RequestStateUpdater;
    private adGroupsRequestStateUpdater: RequestStateUpdater;
    private conversionPixelsRequestStateUpdater: RequestStateUpdater;

    constructor(
        private rulesService: RulesService,
        private publisherGroupsService: PublisherGroupsService,
        private conversionPixelService: ConversionPixelsService,
        private accountService: AccountService,
        private campaignService: CampaignService,
        private adGroupService: AdGroupService,
        private authStore: AuthStore
    ) {
        super(new RuleEditFormStoreState());
        this.requestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this
        );
        this.publisherGroupsRequestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this,
            'publisherGroupsRequests'
        );
        this.conversionPixelsRequestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this,
            'conversionPixelsRequests'
        );
        this.accountsRequestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this,
            'accountsRequests'
        );
        this.campaignsRequestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this,
            'campaignsRequests'
        );
        this.adGroupsRequestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this,
            'adGroupsRequests'
        );
    }

    initStore(
        agencyId: string | null,
        accountId: string | null,
        rule: Partial<Rule>,
        entityId: string,
        entityName: string,
        entityType: EntityType
    ) {
        const hasAgencyScope = this.authStore.hasAgencyScope(agencyId);

        this.loadAccounts(agencyId).then(accounts => {
            if (commonHelpers.isDefined(rule.id)) {
                this.setState({
                    ...this.state,
                    agencyId: agencyId,
                    accountId: accountId,
                    isReadOnly: this.authStore.hasReadOnlyAccessOn(
                        agencyId,
                        rule.accountId
                    ),
                    hasAgencyScope: hasAgencyScope,
                    scopeState: rule.agencyId
                        ? ScopeSelectorState.AGENCY_SCOPE
                        : ScopeSelectorState.ACCOUNT_SCOPE,
                    availablePublisherGroups: this.prepareAvailablePublisherGroups(
                        rule.publisherGroup,
                        this.state.availablePublisherGroups
                    ), // prefill with publisher group object if set
                    availableConditions: rule.targetType
                        ? this.getConditionsForTarget(rule.targetType)
                        : null,
                    rule: {
                        ...this.state.rule,
                        ...rule,
                    },
                    accounts: accounts,
                });
            } else {
                let entities = {...this.state.rule.entities};

                const ruleEntityType = ENTITY_TYPE_TEXT[entityType];
                if (ruleEntityType) {
                    entities = {
                        ...this.state.rule.entities,
                        [ruleEntityType]: {
                            included: [{id: entityId, name: entityName}],
                        },
                    };
                }

                this.setState({
                    ...this.state,
                    agencyId: agencyId,
                    accountId: accountId,
                    hasAgencyScope: hasAgencyScope,
                    isReadOnly: false,
                    scopeState:
                        agencyId && hasAgencyScope
                            ? ScopeSelectorState.AGENCY_SCOPE
                            : ScopeSelectorState.ACCOUNT_SCOPE,
                    rule: {
                        ...this.state.rule,
                        agencyId: !hasAgencyScope ? null : agencyId,
                        accountId:
                            agencyId && hasAgencyScope ? null : accountId,
                        entities: entities,
                    },
                    accounts: accounts,
                });
            }
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

        let actionFrequency = null;
        if (
            [
                RuleActionType.TurnOff,
                RuleActionType.Blacklist,
                RuleActionType.AddToPublisherGroup,
            ].includes(targetActionType.actionType)
        ) {
            actionFrequency = RuleActionFrequency.Days7;
        }

        this.setState({
            ...this.state,
            availableConditions: availableConditions,
            rule: {
                ...this.state.rule,
                targetType: targetActionType.targetType,
                actionType: targetActionType.actionType,
                actionFrequency: actionFrequency,
                changeStep: null,
                changeLimit: null,
                sendEmailRecipients: [],
                sendEmailSubject: null,
                sendEmailBody: null,
                publisherGroup: null,
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

    setPublisherGroup(publisherGroup: PublisherGroup) {
        this.patchState(publisherGroup, 'rule', 'publisherGroup');
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

    setRuleScope(scopeState: ScopeSelectorState) {
        this.setState({
            ...this.state,
            scopeState: scopeState,
            rule: {
                ...this.state.rule,
                agencyId:
                    scopeState === ScopeSelectorState.AGENCY_SCOPE
                        ? this.state.agencyId
                        : null,
                accountId:
                    scopeState === ScopeSelectorState.ACCOUNT_SCOPE
                        ? commonHelpers.getValueOrDefault(
                              this.state.accountId,
                              this.state.accounts[0].id
                          )
                        : null,
            },
        });
    }

    setRuleAccount(accountId: string) {
        this.patchState(accountId, 'rule', 'accountId');
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
                            this.prepareAvailablePublisherGroups(
                                this.state.rule.publisherGroup,
                                publisherGroups
                            ),
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

    loadAvailableConversionPixels(
        keyword: string | null
    ): Promise<ConversionPixel[]> {
        return new Promise<ConversionPixel[]>((resolve, reject) => {
            this.conversionPixelService
                .list(
                    this.state.agencyId,
                    this.state.accountId,
                    commonHelpers.isDefined(keyword) ? keyword.trim() : null,
                    this.conversionPixelsRequestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (conversionPixels: ConversionPixel[]) => {
                        this.patchState(
                            conversionPixels,
                            'availableConversionPixels'
                        );
                        resolve();
                    },
                    () => {
                        reject();
                    }
                );
        });
    }

    getRuleEntitySelectorItems(): EntitySelectorItem[] {
        const entities: EntitySelectorItem[] = [];
        [EntityType.ACCOUNT, EntityType.CAMPAIGN, EntityType.AD_GROUP].forEach(
            entityType => {
                const ruleEntityType = ENTITY_TYPE_TEXT[entityType];
                entities.push(
                    ...(
                        this.state.rule.entities[ruleEntityType]?.included || []
                    ).map((ruleEntity: RuleEntity) => {
                        return {
                            id: ruleEntity.id,
                            name: ruleEntity.name,
                            type: entityType,
                        };
                    })
                );
            }
        );
        return entities;
    }

    searchEntities(keyword: string | null = null): void {
        keyword = keyword ? keyword.trim() : null;
        Promise.all([
            this.loadAccounts(this.state.agencyId, keyword),
            this.loadCampaigns(
                this.state.agencyId,
                this.state.accountId,
                keyword
            ),
            this.loadAdGroups(
                this.state.agencyId,
                this.state.accountId,
                keyword
            ),
        ]).then((values: [Account[], Campaign[], AdGroup[]]) => {
            const entityItems: EntitySelectorItem[] = [];
            [
                EntityType.ACCOUNT,
                EntityType.CAMPAIGN,
                EntityType.AD_GROUP,
            ].forEach((entityType, index) => {
                entityItems.push(
                    ...(values[index] as Array<
                        Account | Campaign | AdGroup
                    >).map(entity => {
                        return {
                            id: entity.id,
                            name: entity.name,
                            type: entityType,
                        };
                    })
                );
            });
            this.patchState(entityItems, 'availableEntities');
        });
    }

    clearAvailableEntities() {
        this.patchState([], 'availableEntities');
    }

    addRuleEntity(entitySelectorItem: EntitySelectorItem): void {
        const ruleEntity: RuleEntity = {
            id: entitySelectorItem.id,
            name: entitySelectorItem.name,
        };

        const entities = clone(this.state.rule.entities);
        const ruleEntityType = ENTITY_TYPE_TEXT[entitySelectorItem.type];
        entities[ruleEntityType].included.push(ruleEntity);

        this.patchState(entities, 'rule', 'entities');
    }

    removeRuleEntity(entitySelectorItem: EntitySelectorItem): void {
        const entities = clone(this.state.rule.entities);
        const ruleEntityType = ENTITY_TYPE_TEXT[entitySelectorItem.type];
        const entityRemoveIndex = entities[ruleEntityType].included.findIndex(
            (entity: RuleEntity) => entity.id === entitySelectorItem.id
        );
        if (entityRemoveIndex !== -1) {
            entities[ruleEntityType].included.splice(entityRemoveIndex, 1);
            this.patchState(entities, 'rule', 'entities');
        }
        this.patchState(entities, 'rule', 'entities');
    }

    saveEntity(): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.rulesService
                .save(this.state.rule, this.requestStateUpdater)
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

    private loadAccounts(
        agencyId: string,
        keyword: string | null = null
    ): Promise<Account[]> {
        return new Promise<Account[]>((resolve, reject) => {
            const offset = 0;
            const limit = 500;
            this.accountService
                .list(
                    agencyId,
                    offset,
                    limit,
                    keyword,
                    false,
                    this.accountsRequestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (accounts: Account[]) => {
                        resolve(accounts);
                    },
                    () => {
                        reject();
                    }
                );
        });
    }

    private loadCampaigns(
        agencyId: string,
        accountId: string,
        keyword: string | null
    ): Promise<Campaign[]> {
        return new Promise<Campaign[]>((resolve, reject) => {
            this.campaignService
                .list(
                    agencyId,
                    accountId,
                    null,
                    null,
                    keyword,
                    this.campaignsRequestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (campaigns: Campaign[]) => {
                        resolve(campaigns);
                    },
                    () => {
                        reject();
                    }
                );
        });
    }

    private loadAdGroups(
        agencyId: string,
        accountId: string,
        keyword: string | null
    ): Promise<AdGroup[]> {
        return new Promise<AdGroup[]>((resolve, reject) => {
            this.adGroupService
                .list(
                    agencyId,
                    accountId,
                    null,
                    null,
                    keyword,
                    this.adGroupsRequestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (adGroups: AdGroup[]) => {
                        resolve(adGroups);
                    },
                    () => {
                        reject();
                    }
                );
        });
    }

    private prepareAvailablePublisherGroups(
        publisherGroup: PublisherGroup,
        availablePublisherGroups: PublisherGroup[]
    ): PublisherGroup[] {
        if (
            publisherGroup &&
            !availablePublisherGroups.some(pg => pg.id === publisherGroup.id)
        ) {
            availablePublisherGroups.unshift(publisherGroup);
        }
        return availablePublisherGroups;
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
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.VideoStart],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.VideoFirstQuartile
            ],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.VideoMidpoint],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.VideoThirdQuartile
            ],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.VideoComplete],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.VideoStartPercent],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.VideoFirstQuartilePercent
            ],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.VideoMidpointPercent
            ],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.VideoThirdQuartilePercent
            ],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.VideoCompletePercent
            ],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.AvgCpv],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.AvgCpcv],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.Mrc50Measurable],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.Mrc50Viewable],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.Mrc50MeasurablePercent
            ],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.Mrc50ViewablePercent
            ],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.Mrc50Vcpm],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.Conversions],
            RULE_CONDITIONS_OPTIONS[
                RuleConditionOperandType.AvgCostPerConversion
            ],
            RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.Roas],
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

        if (
            [
                RuleTargetType.Ad,
                RuleTargetType.AdGroup,
                RuleTargetType.AdGroupSource,
                RuleTargetType.AdGroupPublisher,
            ].includes(target)
        ) {
            conditions.push(
                RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.Visits],
                RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.UniqueUsers],
                RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.NewUsers],
                RULE_CONDITIONS_OPTIONS[
                    RuleConditionOperandType.ReturningUsers
                ],
                RULE_CONDITIONS_OPTIONS[
                    RuleConditionOperandType.PercentNewUsers
                ],
                RULE_CONDITIONS_OPTIONS[
                    RuleConditionOperandType.ClickDiscrepancy
                ],
                RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.Pageviews],
                RULE_CONDITIONS_OPTIONS[
                    RuleConditionOperandType.PageviewsPerVisit
                ],
                RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.BouncedVisits],
                RULE_CONDITIONS_OPTIONS[
                    RuleConditionOperandType.NonBouncedVisits
                ],
                RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.BounceRate],
                RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.TotalSeconds],
                RULE_CONDITIONS_OPTIONS[RuleConditionOperandType.TimeOnSite],
                RULE_CONDITIONS_OPTIONS[
                    RuleConditionOperandType.AvgCostPerVisit
                ],
                RULE_CONDITIONS_OPTIONS[
                    RuleConditionOperandType.AvgCostPerNewVisitor
                ],
                RULE_CONDITIONS_OPTIONS[
                    RuleConditionOperandType.AvgCostPerPageview
                ],
                RULE_CONDITIONS_OPTIONS[
                    RuleConditionOperandType.AvgCostPerNonBouncedVisit
                ],
                RULE_CONDITIONS_OPTIONS[
                    RuleConditionOperandType.AvgCostPerMinute
                ],
                RULE_CONDITIONS_OPTIONS[
                    RuleConditionOperandType.AvgCostPerUniqueUser
                ]
            );
        }

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
