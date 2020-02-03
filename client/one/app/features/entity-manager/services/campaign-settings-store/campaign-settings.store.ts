import {Injectable, OnDestroy} from '@angular/core';
import {Store} from 'rxjs-observable-store';
import {Subject} from 'rxjs';
import {CampaignSettingsStoreState} from './campaign-settings.store.state';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import * as storeHelpers from '../../../../shared/helpers/store.helpers';
import {CampaignService} from '../../../../core/entities/services/campaign/campaign.service';
import {ConversionPixelsService} from '../../../../core/conversion-pixels/services/conversion-pixels.service';
import {takeUntil} from 'rxjs/operators';
import {CampaignWithExtras} from '../../../../core/entities/types/campaign/campaign-with-extras';
import * as clone from 'clone';
import {Campaign} from '../../../../core/entities/types/campaign/campaign';
import {HttpErrorResponse} from '@angular/common/http';
import {CampaignSettingsStoreFieldsErrorsState} from './campaign-settings.store.fields-errors-state';
import * as deepEqual from 'fast-deep-equal';
import {CampaignGoal} from '../../../../core/entities/types/campaign/campaign-goal';
import {ChangeEvent} from '../../../../shared/types/change-event';
import {
    CampaignGoalKPI,
    CampaignType,
    IabCategory,
    Language,
} from '../../../../app.constants';
import {ConversionPixelChangeEvent} from '../../types/conversion-pixel-change-event';
import {CampaignTracking} from '../../../../core/entities/types/campaign/campaign-tracking';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {CampaignBudget} from '../../../../core/entities/types/campaign/campaign-budget';
import * as moment from 'moment';
import * as messagesHelpers from '../../helpers/messages.helpers';
import {IncludedExcluded} from '../../../../core/entities/types/common/included-excluded';
import {Deal} from '../../../../core/deals/types/deal';
import {DealsService} from '../../../../core/deals/services/deals.service';
import {SourcesService} from '../../../../core/sources/services/sources.service';

@Injectable()
export class CampaignSettingsStore extends Store<CampaignSettingsStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<void> = new Subject();
    private requestStateUpdater: RequestStateUpdater;
    private dealsRequestStateUpdater: RequestStateUpdater;
    private sourcesRequestStateUpdater: RequestStateUpdater;
    private originalEntity: Campaign;

    constructor(
        private campaignService: CampaignService,
        private conversionPixelsService: ConversionPixelsService,
        private dealsService: DealsService,
        private sourcesService: SourcesService
    ) {
        super(new CampaignSettingsStoreState());
        this.requestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this
        );
        this.dealsRequestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this,
            'dealsRequests'
        );
        this.sourcesRequestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this,
            'sourcesRequests'
        );
    }

    loadEntityDefaults(accountId: string) {
        this.campaignService
            .defaults(accountId, this.requestStateUpdater)
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe(
                campaignWithExtras => {
                    this.setState({
                        ...this.state,
                        entity: campaignWithExtras.campaign,
                        extras: campaignWithExtras.extras,
                    });
                    this.loadConversionPixelsForAccount(
                        this.state.entity.accountId
                    );
                    this.loadSources(this.state.extras.agencyId);
                },
                error => {}
            );
    }

    loadEntity(id: string) {
        this.campaignService
            .get(id, this.requestStateUpdater)
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe(
                (campaignWithExtras: CampaignWithExtras) => {
                    this.originalEntity = clone(campaignWithExtras.campaign);
                    this.setState({
                        ...this.state,
                        entity: campaignWithExtras.campaign,
                        extras: campaignWithExtras.extras,
                    });
                    this.loadConversionPixelsForAccount(
                        this.state.entity.accountId
                    );
                    this.loadSources(this.state.extras.agencyId);
                },
                error => {}
            );
    }

    validateEntity() {
        const entity = storeHelpers.getNewStateWithoutNull(this.state.entity);
        this.campaignService
            .validate(entity, this.requestStateUpdater)
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe(
                () => {
                    this.patchState(
                        new CampaignSettingsStoreFieldsErrorsState(),
                        'fieldsErrors'
                    );
                },
                (error: HttpErrorResponse) => {
                    const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                        new CampaignSettingsStoreFieldsErrorsState(),
                        error
                    );
                    this.patchState(fieldsErrors, 'fieldsErrors');
                }
            );
    }

    saveEntity(): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            if (!this.isAutopilotChangeConfirmed()) {
                resolve(false);
                return;
            }
            this.campaignService
                .save(this.state.entity, this.requestStateUpdater)
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (campaign: Campaign) => {
                        this.setState({
                            ...this.state,
                            entity: campaign,
                            fieldsErrors: new CampaignSettingsStoreFieldsErrorsState(),
                        });
                        resolve(true);
                    },
                    (error: HttpErrorResponse) => {
                        const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                            new CampaignSettingsStoreFieldsErrorsState(),
                            error
                        );
                        this.patchState(fieldsErrors, 'fieldsErrors');
                        resolve(false);
                    }
                );
        });
    }

    archiveEntity(): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            this.campaignService
                .archive(this.state.entity.id, this.requestStateUpdater)
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    () => {
                        resolve(true);
                    },
                    (error: HttpErrorResponse) => {
                        const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                            new CampaignSettingsStoreFieldsErrorsState(),
                            error
                        );
                        this.patchState(fieldsErrors, 'fieldsErrors');
                        resolve(false);
                    }
                );
        });
    }

    loadSources(agencyId: string) {
        this.sourcesService
            .list(agencyId, this.sourcesRequestStateUpdater)
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe(
                sources => {
                    this.setState({
                        ...this.state,
                        sources: sources,
                    });
                },
                error => {}
            );
    }

    loadAvailableDeals(keyword: string | null): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            const isKeywordDefined = commonHelpers.isDefined(keyword);
            this.dealsService
                .list(
                    this.state.extras.agencyId,
                    null,
                    !isKeywordDefined ? 0 : null,
                    !isKeywordDefined ? 10 : null,
                    !isKeywordDefined ? null : keyword.trim(),
                    this.dealsRequestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (deals: Deal[]) => {
                        this.patchState(deals, 'availableDeals');
                        resolve();
                    },
                    error => {
                        reject();
                    }
                );
        });
    }

    addDeal(deal: Deal | null) {
        this.validateEntity();
        if (!commonHelpers.isDefined(deal)) {
            deal = {
                id: null,
                dealId: null,
                agencyId: null,
                accountId: null,
                description: null,
                name: null,
                source: null,
                floorPrice: null,
                validFromDate: null,
                validToDate: null,
                createdDt: null,
                modifiedDt: null,
                createdBy: null,
                numOfAccounts: null,
                numOfCampaigns: null,
                numOfAdgroups: null,
            };
        }
        this.setState({
            ...this.state,
            entity: {
                ...this.state.entity,
                deals: [...this.state.entity.deals, deal],
            },
            availableDeals: [],
        });
    }

    removeDeal(deal: Deal) {
        const deals = this.state.entity.deals.filter(item => {
            return item !== deal;
        });
        this.patchState(deals, 'entity', 'deals');
        this.validateEntity();
    }

    changeDeal($event: ChangeEvent<Deal>) {
        const deals = this.state.entity.deals.map(deal => {
            if (deal === $event.target) {
                return {
                    ...$event.target,
                    ...$event.changes,
                };
            } else {
                return deal;
            }
        });
        this.patchState(deals, 'entity', 'deals');
        this.validateEntity();
    }

    hasDealError(index: number): boolean {
        if (this.state.fieldsErrors.deals.length > 0) {
            const dealErrors = (this.state.fieldsErrors.deals || [])[index];
            if (
                commonHelpers.isDefined(dealErrors) &&
                Object.keys(dealErrors).length > 0
            ) {
                return true;
            }
        }
        return false;
    }

    doEntitySettingsHaveUnsavedChanges(): boolean {
        if (!this.originalEntity) {
            return false;
        }
        return !deepEqual(this.originalEntity, this.state.entity);
    }

    setName(name: string) {
        this.patchState(name, 'entity', 'name');
        this.validateEntity();
    }

    setType(type: CampaignType) {
        this.patchState(type, 'entity', 'type');
        this.validateEntity();
    }

    setCampaignManager(campaignManager: string) {
        this.patchState(campaignManager, 'entity', 'campaignManager');
        this.validateEntity();
    }

    setIabCategory(iabCategory: IabCategory) {
        this.patchState(iabCategory, 'entity', 'iabCategory');
        this.validateEntity();
    }

    setLanguage(language: Language) {
        this.patchState(language, 'entity', 'language');
        this.validateEntity();
    }

    setFrequencyCapping(frequencyCapping: string) {
        let frequencyCappingNumber = null;
        if (commonHelpers.isNotEmpty(frequencyCapping)) {
            frequencyCappingNumber = parseInt(frequencyCapping, 10) || null;
        }
        this.patchState(frequencyCappingNumber, 'entity', 'frequencyCapping');
        this.validateEntity();
    }

    setAutopilot(autopilot: boolean) {
        this.patchState(autopilot, 'entity', 'autopilot');
        this.validateEntity();
    }

    setPublisherGroupsTargeting(publisherGroupsTargeting: {
        whitelistedPublisherGroups?: number[];
        blacklistedPublisherGroups?: number[];
    }) {
        const newPublisherGroupsTargeting: IncludedExcluded<number[]> = {
            included: publisherGroupsTargeting.whitelistedPublisherGroups
                ? publisherGroupsTargeting.whitelistedPublisherGroups
                : this.state.entity.targeting.publisherGroups.included,
            excluded: publisherGroupsTargeting.blacklistedPublisherGroups
                ? publisherGroupsTargeting.blacklistedPublisherGroups
                : this.state.entity.targeting.publisherGroups.excluded,
        };

        this.patchState(
            newPublisherGroupsTargeting,
            'entity',
            'targeting',
            'publisherGroups'
        );
        this.validateEntity();
    }

    changeCampaignTracking($event: ChangeEvent<CampaignTracking>) {
        const tracking = {
            ...$event.target,
            ...$event.changes,
        };
        this.patchState(tracking, 'entity', 'tracking');
        this.validateEntity();
    }

    /**
     * Start: Conversion Pixels
     */

    loadConversionPixelsForAccount(accountId: string) {
        this.conversionPixelsService
            .list(accountId, this.requestStateUpdater)
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe(
                conversionPixels => {
                    this.patchState(conversionPixels, 'conversionPixels');
                },
                error => {}
            );
    }

    createConversionPixel($event: ConversionPixelChangeEvent) {
        const index = this.state.entity.goals.indexOf($event.campaignGoal);
        const requestStateUpdater = this.getConversionPixelsRequestStateUpdater(
            index
        );

        this.conversionPixelsService
            .create(
                this.state.entity.accountId,
                $event.conversionPixelName,
                requestStateUpdater
            )
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe(
                conversionPixel => {
                    const goals = this.state.entity.goals.map(item => {
                        if (item === $event.campaignGoal) {
                            return {
                                ...item,
                                conversionGoal: {
                                    ...$event.campaignGoal.conversionGoal,
                                    conversionWindow: null,
                                    goalId: conversionPixel.id,
                                    pixelUrl: null,
                                    name: null,
                                },
                            };
                        }
                        return item;
                    });
                    const conversionPixels = [
                        ...this.state.conversionPixels,
                        conversionPixel,
                    ];
                    const conversionPixelsErrors = this.state.conversionPixelsErrors.filter(
                        error => {
                            return (
                                this.state.conversionPixelsErrors.indexOf(
                                    error
                                ) !== index
                            );
                        }
                    );

                    this.setState({
                        ...this.state,
                        entity: {
                            ...this.state.entity,
                            goals: goals,
                        },
                        conversionPixels: conversionPixels,
                        conversionPixelsErrors: conversionPixelsErrors,
                    });
                },
                (error: HttpErrorResponse) => {
                    const index = this.state.entity.goals.indexOf(
                        $event.campaignGoal
                    );
                    const nameError =
                        commonHelpers.isDefined(error.error) &&
                        commonHelpers.isDefined(error.error.details)
                            ? error.error.details.name
                            : null;

                    const conversionPixelsErrors = clone(
                        this.state.conversionPixelsErrors
                    );
                    conversionPixelsErrors[index] = {
                        name: nameError,
                    };

                    this.patchState(
                        conversionPixelsErrors,
                        'conversionPixelsErrors'
                    );
                }
            );
    }

    cancelConversionPixelCreation($event: ConversionPixelChangeEvent) {
        const index = this.state.entity.goals.indexOf($event.campaignGoal);
        const conversionPixelsErrors = this.state.conversionPixelsErrors.filter(
            error => {
                return (
                    this.state.conversionPixelsErrors.indexOf(error) !== index
                );
            }
        );

        this.patchState(conversionPixelsErrors, 'conversionPixelsErrors');
    }

    /**
     * End: Conversion Pixels
     */

    /**
     * Start: Campaign Goals
     */

    createGoal() {
        this.validateEntity();
        const goals = this.state.entity.goals.map(item => {
            return {
                ...item,
                primary: false,
            };
        });
        goals.push({
            id: null,
            type: null,
            value: null,
            primary: true,
            conversionGoal: null,
        });
        this.patchState(goals, 'entity', 'goals');
    }

    setPrimaryGoal($event: CampaignGoal) {
        const goals = this.state.entity.goals.map(item => {
            return {
                ...item,
                primary: item === $event,
            };
        });
        this.patchState(goals, 'entity', 'goals');
        this.validateEntity();
    }

    changeGoal($event: ChangeEvent<CampaignGoal>) {
        const goals = this.state.entity.goals.map(item => {
            if (item === $event.target) {
                if ($event.changes.type) {
                    let conversionGoal = null;
                    if ($event.changes.type === CampaignGoalKPI.CPA) {
                        conversionGoal = {
                            type: null,
                            conversionWindow: null,
                            goalId: null,
                            pixelUrl: null,
                            name: null,
                        };
                    }
                    return {
                        ...item,
                        value: this.state.extras.goalsDefaults[
                            $event.changes.type
                        ],
                        type: $event.changes.type,
                        conversionGoal: conversionGoal,
                    };
                }
                return {
                    ...item,
                    ...$event.changes,
                };
            }
            return item;
        });
        this.patchState(goals, 'entity', 'goals');
        this.validateEntity();
    }

    deleteGoal(campaignGoal: CampaignGoal) {
        const goals = this.state.entity.goals.filter(item => {
            return item !== campaignGoal;
        });
        if (campaignGoal.primary && goals.length > 0) {
            goals[0] = {
                ...goals[0],
                primary: true,
            };
        }
        this.patchState(goals, 'entity', 'goals');
        this.validateEntity();
    }

    /**
     * End: Campaign Goals
     */

    /**
     * Start: Campaign budget
     */

    isAnyAccountCreditAvailable(): boolean {
        return (
            this.state.extras.accountCredits.filter(item => {
                return item.isAvailable;
            }).length > 0
        );
    }

    createBudget() {
        this.validateEntity();
        const availableCredits =
            this.state.extras.accountCredits.filter(item => {
                return item.isAvailable;
            }) || [];
        if (availableCredits.length === 0) {
            return;
        }
        const todayDate = moment().toDate();
        const budgets: CampaignBudget[] = [
            ...this.state.entity.budgets,
            {
                id: null,
                creditId: availableCredits[0].id,
                startDate:
                    availableCredits[0].startDate > todayDate
                        ? availableCredits[0].startDate
                        : todayDate,
                endDate: null,
                amount: null,
                margin: null,
                comment: null,
                canEditStartDate: true,
                canEditEndDate: true,
                canEditAmount: true,
            },
        ];
        this.patchState(budgets, 'entity', 'budgets');
    }

    updateBudget($event: ChangeEvent<CampaignBudget>) {
        const budgets = this.state.entity.budgets.map(budget => {
            if (budget === $event.target) {
                return {
                    ...budget,
                    ...$event.changes,
                };
            }
            return budget;
        });
        this.patchState(budgets, 'entity', 'budgets');
        this.validateEntity();
    }

    deleteBudget(campaignBudget: CampaignBudget) {
        const budgets = this.state.entity.budgets.filter(item => {
            return item !== campaignBudget;
        });
        this.patchState(budgets, 'entity', 'budgets');
        this.validateEntity();
    }

    /**
     * End: Campaign budget
     */

    ngOnDestroy() {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    private getConversionPixelsRequestStateUpdater(
        index: number
    ): RequestStateUpdater {
        return (requestName, requestState) => {
            const conversionPixelsRequests = clone(
                this.state.conversionPixelsRequests
            );
            conversionPixelsRequests[index] = {
                ...conversionPixelsRequests[index],
                [requestName]: requestState,
            };
            this.patchState(
                conversionPixelsRequests,
                'conversionPixelsRequests'
            );
        };
    }

    private isAutopilotChangeConfirmed(): boolean {
        if (
            !this.originalEntity ||
            this.state.entity.autopilot === this.originalEntity.autopilot
        ) {
            return true;
        }
        return confirm(
            messagesHelpers.getAutopilotChangeConfirmMessage(
                this.state.entity.autopilot
            )
        );
    }
}
