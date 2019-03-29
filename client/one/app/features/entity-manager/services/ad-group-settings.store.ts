import {Injectable, OnDestroy, Inject} from '@angular/core';
import {Store} from 'rxjs-observable-store';
import {Subject} from 'rxjs';
import {AdGroupSettingsStoreState} from './ad-group-settings.store.state';
import {AdGroupService} from '../../../core/entities/services/ad-group.service';
import {HttpErrorResponse} from '@angular/common/http';
import {AdGroup} from '../../../core/entities/types/ad-group/ad-group';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import * as storeHelpers from '../../../shared/helpers/store.helpers';
import {AdGroupWithExtras} from '../../../core/entities/types/ad-group/ad-group-with-extras';
import {
    AdGroupAutopilotState,
    DeliveryType,
    BiddingType,
} from '../../../app.constants';
import {AdGroupSettingsStoreFieldsErrorsState} from './ad-group-settings.store.fields-errors-state';
import {AdGroupDayparting} from '../../../core/entities/types/ad-group/ad-group-dayparting';

@Injectable()
export class AdGroupSettingsStore extends Store<AdGroupSettingsStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<void> = new Subject();
    private requestStateUpdater: RequestStateUpdater;

    constructor(
        private adGroupService: AdGroupService,
        @Inject('zemNavigationNewService') private zemNavigationNewService: any
    ) {
        super(new AdGroupSettingsStoreState());
        this.requestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this
        );
    }

    loadEntityDefaults(campaignId: number): void {
        this.adGroupService
            .defaults(campaignId, this.requestStateUpdater)
            .subscribe(
                (adGroupWithExtras: AdGroupWithExtras) => {
                    this.setState({
                        ...this.state,
                        entity: adGroupWithExtras.adGroup,
                        extras: adGroupWithExtras.extras,
                    });
                },
                error => {}
            );
    }

    loadEntity(id: number): void {
        this.adGroupService.get(id, this.requestStateUpdater).subscribe(
            (adGroupWithExtras: AdGroupWithExtras) => {
                this.setState({
                    ...this.state,
                    entity: adGroupWithExtras.adGroup,
                    extras: adGroupWithExtras.extras,
                });
            },
            error => {}
        );
    }

    validateEntity(): void {
        this.adGroupService
            .validate(this.state.entity, this.requestStateUpdater)
            .subscribe(
                () => {
                    this.updateState(
                        new AdGroupSettingsStoreFieldsErrorsState(),
                        'fieldsErrors'
                    );
                },
                (error: HttpErrorResponse) => {
                    const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                        new AdGroupSettingsStoreFieldsErrorsState(),
                        error
                    );
                    this.updateState(fieldsErrors, 'fieldsErrors');
                }
            );
    }

    saveEntity(): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            this.adGroupService
                .save(this.state.entity, this.requestStateUpdater)
                .subscribe(
                    (adGroup: AdGroup) => {
                        this.setState({
                            ...this.state,
                            entity: adGroup,
                            fieldsErrors: new AdGroupSettingsStoreFieldsErrorsState(),
                        });
                        resolve(true);
                    },
                    (error: HttpErrorResponse) => {
                        const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                            new AdGroupSettingsStoreFieldsErrorsState(),
                            error
                        );
                        this.updateState(fieldsErrors, 'fieldsErrors');
                        resolve(false);
                    }
                );
        });
    }

    archiveEntity(): void {
        this.adGroupService
            .archive(this.state.entity.id, this.requestStateUpdater)
            .subscribe(
                () => {
                    this.zemNavigationNewService.refreshState();
                },
                (error: HttpErrorResponse) => {
                    const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                        new AdGroupSettingsStoreFieldsErrorsState(),
                        error
                    );
                    this.updateState(fieldsErrors, 'fieldsErrors');
                }
            );
    }

    isAdGroupAutopilotEnabled() {
        return (
            !this.state.extras.isCampaignAutopilotEnabled &&
            this.state.entity.autopilot &&
            this.state.entity.autopilot.state ===
                AdGroupAutopilotState.ACTIVE_CPC_BUDGET
        );
    }

    setStartDate(startDate: Date) {
        this.updateState(startDate, 'entity', 'startDate');
    }

    setEndDate(endDate: Date) {
        this.updateState(endDate, 'entity', 'endDate');
    }

    setDeliveryType(deliveryType: DeliveryType) {
        this.updateState(deliveryType, 'entity', 'deliveryType');
    }

    setDayparting(dayparting: AdGroupDayparting) {
        this.updateState(dayparting, 'entity', 'dayparting');
    }

    setBiddingType(biddingType: BiddingType) {
        this.updateState(biddingType, 'entity', 'biddingType');
    }

    setMaxCpc(maxCpc: string) {
        this.updateState(maxCpc, 'entity', 'maxCpc');
    }

    setMaxCpm(maxCpm: string) {
        this.updateState(maxCpm, 'entity', 'maxCpm');
    }

    setAutopilotDailyBudget(dailyBudget: string) {
        this.updateState(dailyBudget, 'entity', 'autopilot', 'dailyBudget');
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }
}
