import {Injectable, OnDestroy, Inject} from '@angular/core';
import {HttpErrorResponse} from '@angular/common/http';
import {Store} from 'rxjs-observable-store';
import {Subject} from 'rxjs';
import * as deepEqual from 'fast-deep-equal';
import * as clone from 'clone';
import {AdGroupSettingsStoreState} from './ad-group-settings.store.state';
import {AdGroupService} from '../../../core/entities/services/ad-group.service';
import {AdGroup} from '../../../core/entities/types/ad-group/ad-group';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import * as storeHelpers from '../../../shared/helpers/store.helpers';
import {AdGroupWithExtras} from '../../../core/entities/types/ad-group/ad-group-with-extras';
import {
    AdGroupAutopilotState,
    DeliveryType,
    BiddingType,
    InterestCategory,
    AdGroupState,
} from '../../../app.constants';
import {AdGroupSettingsStoreFieldsErrorsState} from './ad-group-settings.store.fields-errors-state';
import {AdGroupDayparting} from '../../../core/entities/types/ad-group/ad-group-dayparting';
import {OperatingSystem} from '../../../core/entities/types/common/operating-system';
import {IncludedExcluded} from '../../../core/entities/types/common/included-excluded';
import {TargetRegions} from '../../../core/entities/types/common/target-regions';
import * as messagesHelpers from '../helpers/messages.helpers';

@Injectable()
export class AdGroupSettingsStore extends Store<AdGroupSettingsStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<void> = new Subject();
    private requestStateUpdater: RequestStateUpdater;
    private originalEntity: AdGroup;

    constructor(
        private adGroupService: AdGroupService,
        @Inject('zemNavigationNewService') private zemNavigationNewService: any
    ) {
        super(new AdGroupSettingsStoreState());
        this.requestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this
        );
    }

    loadEntityDefaults(campaignId: number) {
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

    loadEntity(id: number) {
        this.adGroupService.get(id, this.requestStateUpdater).subscribe(
            (adGroupWithExtras: AdGroupWithExtras) => {
                this.originalEntity = clone(adGroupWithExtras.adGroup);
                this.setState({
                    ...this.state,
                    entity: adGroupWithExtras.adGroup,
                    extras: adGroupWithExtras.extras,
                });
            },
            error => {}
        );
    }

    validateEntity() {
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
            if (!this.isManageRtbSourcesAsOneChangeConfirmed()) {
                resolve(false);
                return;
            }
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

    archiveEntity() {
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

    doEntitySettingsHaveUnsavedChanges(): boolean {
        if (!this.originalEntity) {
            return false;
        }
        return !deepEqual(this.originalEntity, this.state.entity);
    }

    isAdGroupAutopilotEnabled() {
        return (
            !this.state.extras.isCampaignAutopilotEnabled &&
            this.state.entity.autopilot &&
            this.state.entity.autopilot.state ===
                AdGroupAutopilotState.ACTIVE_CPC_BUDGET
        );
    }

    setName(name: string) {
        this.updateState(name, 'entity', 'name');
    }

    setLanguageMatching(matchingEnabled: boolean) {
        this.updateState(
            matchingEnabled,
            'entity',
            'targeting',
            'language',
            'matchingEnabled'
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

    setDailyClickCap(clickCap: string) {
        this.updateState(
            clickCap,
            'entity',
            'clickCappingDailyAdGroupMaxClicks'
        );
    }

    setImpressionFrequencyCap(impressionFrequencyCap: string) {
        this.updateState(impressionFrequencyCap, 'entity', 'frequencyCapping');
    }

    isDeviceTargetingDifferentFromDefault(): boolean {
        const areTargetDevicesDifferent = !deepEqual(
            this.state.entity.targeting.devices,
            this.state.extras.defaultSettings.targetDevices
        );
        const areTargetOsDifferent = !deepEqual(
            this.state.entity.targeting.os,
            this.state.extras.defaultSettings.targetOs
        );
        const areTargetPlacementsDifferent = !deepEqual(
            this.state.entity.targeting.placements,
            this.state.extras.defaultSettings.targetPlacements
        );

        return (
            areTargetDevicesDifferent ||
            areTargetOsDifferent ||
            areTargetPlacementsDifferent
        );
    }

    setDeviceTargeting(deviceTargeting: {
        targetDevices?: string[];
        targetPlacements?: string[];
        targetOs?: OperatingSystem[];
    }) {
        this.setState({
            ...this.state,
            entity: {
                ...this.state.entity,
                targeting: {
                    ...this.state.entity.targeting,
                    devices: deviceTargeting.targetDevices,
                    placements: deviceTargeting.targetPlacements,
                    os: deviceTargeting.targetOs,
                },
            },
        });
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

        this.updateState(
            newPublisherGroupsTargeting,
            'entity',
            'targeting',
            'publisherGroups'
        );
    }

    setInterestTargeting(interestTargeting: {
        includedInterests?: InterestCategory[];
        excludedInterests?: InterestCategory[];
    }) {
        const newInterestTargeting: IncludedExcluded<InterestCategory[]> = {
            included: interestTargeting.includedInterests
                ? interestTargeting.includedInterests
                : this.state.entity.targeting.interest.included,
            excluded: interestTargeting.excludedInterests
                ? interestTargeting.excludedInterests
                : this.state.entity.targeting.interest.excluded,
        };

        this.updateState(
            newInterestTargeting,
            'entity',
            'targeting',
            'interest'
        );
    }

    setRetargeting(retargeting: {
        includedAudiences?: number[];
        excludedAudiences?: number[];
        includedAdGroups?: number[];
        excludedAdGroups?: number[];
    }) {
        const customAudiences: IncludedExcluded<number[]> = {
            included: retargeting.includedAudiences
                ? retargeting.includedAudiences
                : this.state.entity.targeting.customAudiences.included,
            excluded: retargeting.excludedAudiences
                ? retargeting.excludedAudiences
                : this.state.entity.targeting.customAudiences.excluded,
        };

        const retargetingAdGroups: IncludedExcluded<number[]> = {
            included: retargeting.includedAdGroups
                ? retargeting.includedAdGroups
                : this.state.entity.targeting.retargetingAdGroups.included,
            excluded: retargeting.excludedAdGroups
                ? retargeting.excludedAdGroups
                : this.state.entity.targeting.retargetingAdGroups.excluded,
        };

        this.setState({
            ...this.state,
            entity: {
                ...this.state.entity,
                targeting: {
                    ...this.state.entity.targeting,
                    customAudiences: customAudiences,
                    retargetingAdGroups: retargetingAdGroups,
                },
            },
        });
    }

    setBluekaiTargeting(bluekaiTargeting: any) {
        this.updateState(bluekaiTargeting, 'entity', 'targeting', 'audience');
    }

    setAdGroupAutopilotState(autopilotState: AdGroupAutopilotState) {
        const manageRtbSourcesAsOne =
            autopilotState === AdGroupAutopilotState.ACTIVE_CPC_BUDGET ||
            this.state.entity.manageRtbSourcesAsOne;
        this.setState({
            ...this.state,
            entity: {
                ...this.state.entity,
                autopilot: {
                    ...this.state.entity.autopilot,
                    state: autopilotState,
                },
                manageRtbSourcesAsOne: manageRtbSourcesAsOne,
            },
        });
    }

    setManageRtbSourcesAsOne(manageRtbSourcesAsOne: boolean) {
        this.updateState(
            manageRtbSourcesAsOne,
            'entity',
            'manageRtbSourcesAsOne'
        );
    }

    setTrackingCode(trackingCode: string): void {
        this.updateState(trackingCode, 'entity', 'trackingCode');
    }

    isLocationTargetingDifferentFromDefault(): boolean {
        const areIncludedLocationsDifferent = !deepEqual(
            this.state.entity.targeting.geo.included,
            this.state.extras.defaultSettings.targetRegions
        );
        const areExcludedLocationsDifferent = !deepEqual(
            this.state.entity.targeting.geo.excluded,
            this.state.extras.defaultSettings.exclusionTargetRegions
        );
        return areIncludedLocationsDifferent || areExcludedLocationsDifferent;
    }

    setLocationTargeting(locationTargeting: {
        includedLocations: TargetRegions;
        excludedLocations: TargetRegions;
    }) {
        const geoTargeting: IncludedExcluded<TargetRegions> = {
            included: locationTargeting.includedLocations
                ? locationTargeting.includedLocations
                : this.state.entity.targeting.geo.included,
            excluded: locationTargeting.excludedLocations
                ? locationTargeting.excludedLocations
                : this.state.entity.targeting.geo.excluded,
        };

        this.updateState(geoTargeting, 'entity', 'targeting', 'geo');
    }

    ngOnDestroy() {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    private isManageRtbSourcesAsOneChangeConfirmed(): boolean {
        if (
            this.state.entity.manageRtbSourcesAsOne ===
            this.originalEntity.manageRtbSourcesAsOne
        ) {
            return true;
        }
        return confirm(
            messagesHelpers.getManageRtbSourcesAsOneChangeConfirmMessage(
                this.state.entity.state,
                this.state.entity.manageRtbSourcesAsOne
            )
        );
    }
}
