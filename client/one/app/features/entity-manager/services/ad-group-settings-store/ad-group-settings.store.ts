import {Injectable, OnDestroy} from '@angular/core';
import {HttpErrorResponse} from '@angular/common/http';
import {Store} from 'rxjs-observable-store';
import {Subject, forkJoin, Observable} from 'rxjs';
import {takeUntil} from 'rxjs/operators';
import * as deepEqual from 'fast-deep-equal';
import * as clone from 'clone';
import {AdGroupSettingsStoreState} from './ad-group-settings.store.state';
import {AdGroupService} from '../../../../core/entities/services/ad-group/ad-group.service';
import {AdGroup} from '../../../../core/entities/types/ad-group/ad-group';
import {BidModifiersService} from '../../../../core/bid-modifiers/services/bid-modifiers.service';
import {BidModifierUploadSummary} from '../../../../core/bid-modifiers/types/bid-modifier-upload-summary';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import * as storeHelpers from '../../../../shared/helpers/store.helpers';
import {AdGroupWithExtras} from '../../../../core/entities/types/ad-group/ad-group-with-extras';
import {
    AdGroupAutopilotState,
    DeliveryType,
    BiddingType,
    InterestCategory,
    GeolocationType,
    IncludeExcludeType,
} from '../../../../app.constants';
import {AdGroupSettingsStoreFieldsErrorsState} from './ad-group-settings.store.fields-errors-state';
import {BidModifiersImportErrorState} from './bid-modifiers-import-error-state';
import {AdGroupDayparting} from '../../../../core/entities/types/ad-group/ad-group-dayparting';
import {TargetOperatingSystem} from '../../../../core/entities/types/common/target-operating-system';
import {IncludedExcluded} from '../../../../core/entities/types/common/included-excluded';
import {TargetRegions} from '../../../../core/entities/types/common/target-regions';
import * as messagesHelpers from '../../helpers/messages.helpers';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {DealsService} from '../../../../core/deals/services/deals.service';
import {Deal} from '../../../../core/deals/types/deal';
import {SourcesService} from '../../../../core/sources/services/sources.service';
import {ChangeEvent} from '../../../../shared/types/change-event';
import {OperatingSystem} from '../../components/operating-system/types/operating-system';
import {
    OPERATING_SYSTEMS,
    TARGETING_DEVICE_OPTIONS,
    TARGETING_ENVIRONMENT_OPTIONS,
} from '../../entity-manager.config';
import {isEmpty} from '../../../../shared/helpers/array.helpers';
import {GeolocationsService} from '../../../../core/geolocations/services/geolocations.service';
import {Geolocation} from '../../../../core/geolocations/types/geolocation';
import {
    getGeolocationsKeys,
    getGeotargetingLocationPropertyFromGeolocationType,
    getIncludeExcludePropertyNameFromIncludeExcludeType,
} from '../../helpers/geolocations.helpers';
import {GeolocationSearchParams} from '../../types/geolocation-search-params';
import {Geotargeting} from '../../types/geotargeting';

@Injectable()
export class AdGroupSettingsStore extends Store<AdGroupSettingsStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<void> = new Subject();
    private requestStateUpdater: RequestStateUpdater;
    private dealsRequestStateUpdater: RequestStateUpdater;
    private sourcesRequestStateUpdater: RequestStateUpdater;
    private bidModifierRequestStateUpdater: RequestStateUpdater;
    private locationsRequestStateUpdater: RequestStateUpdater;
    private originalEntity: AdGroup;

    constructor(
        private adGroupService: AdGroupService,
        private dealsService: DealsService,
        private sourcesService: SourcesService,
        private bidModifierService: BidModifiersService,
        private locationService: GeolocationsService
    ) {
        super(new AdGroupSettingsStoreState());
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
        this.bidModifierRequestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this,
            'bidModifiersRequests'
        );
        this.locationsRequestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this,
            'locationsRequests'
        );
    }

    loadEntityDefaults(campaignId: string) {
        this.adGroupService
            .defaults(campaignId, this.requestStateUpdater)
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe(
                (adGroupWithExtras: AdGroupWithExtras) => {
                    this.setState({
                        ...this.state,
                        entity: adGroupWithExtras.adGroup,
                        extras: adGroupWithExtras.extras,
                    });
                    this.loadSources(this.state.extras.agencyId);
                },
                error => {}
            );
    }

    loadEntity(id: string) {
        this.adGroupService
            .get(id, this.requestStateUpdater)
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe(
                (adGroupWithExtras: AdGroupWithExtras) => {
                    this.originalEntity = clone(adGroupWithExtras.adGroup);
                    this.setState({
                        ...this.state,
                        entity: adGroupWithExtras.adGroup,
                        extras: adGroupWithExtras.extras,
                    });
                    this.loadSources(this.state.extras.agencyId);
                    this.loadSelectedLocations(
                        getGeolocationsKeys(this.state.entity.targeting.geo)
                    );
                },
                error => {}
            );
    }

    validateEntity() {
        const entity = storeHelpers.getNewStateWithoutNull(this.state.entity);
        this.adGroupService
            .validate(entity, this.requestStateUpdater)
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe(
                () => {
                    this.patchState(
                        new AdGroupSettingsStoreFieldsErrorsState(),
                        'fieldsErrors'
                    );
                },
                (error: HttpErrorResponse) => {
                    const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                        new AdGroupSettingsStoreFieldsErrorsState(),
                        error
                    );
                    this.patchState(fieldsErrors, 'fieldsErrors');
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
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (adGroup: AdGroup) => {
                        this.setState({
                            ...this.state,
                            entity: adGroup,
                            fieldsErrors: new AdGroupSettingsStoreFieldsErrorsState(),
                        });
                        if (
                            commonHelpers.isDefined(
                                this.state.bidModifiersImportFile
                            )
                        ) {
                            this.importBidModifiersFile().then(
                                (importSuccess: boolean) => {
                                    resolve(importSuccess);
                                }
                            );
                        } else {
                            resolve(true);
                        }
                    },
                    (error: HttpErrorResponse) => {
                        const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                            new AdGroupSettingsStoreFieldsErrorsState(),
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
            this.adGroupService
                .archive(this.state.entity.id, this.requestStateUpdater)
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    () => {
                        resolve(true);
                    },
                    (error: HttpErrorResponse) => {
                        const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                            new AdGroupSettingsStoreFieldsErrorsState(),
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

    loadAvailableDeals(keyword: string = null): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            const isKeywordDefined = commonHelpers.isDefined(keyword);
            this.dealsService
                .list(
                    null,
                    this.state.extras.accountId,
                    !isKeywordDefined ? 0 : null,
                    !isKeywordDefined ? 10 : null,
                    !isKeywordDefined ? null : keyword.trim(),
                    null,
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

    addDeal(deal: Deal = null) {
        this.validateEntity();
        if (!commonHelpers.isDefined(deal)) {
            deal = {
                id: null,
                dealId: null,
                agencyId: null,
                agencyName: null,
                accountId: this.state.extras.accountId,
                accountName: null,
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

    isAdGroupAutopilotEnabled() {
        return (
            !this.state.extras.isCampaignAutopilotEnabled &&
            this.state.entity.autopilot &&
            this.state.entity.autopilot.state ===
                AdGroupAutopilotState.ACTIVE_CPC_BUDGET
        );
    }

    setName(name: string) {
        this.patchState(name, 'entity', 'name');
        this.validateEntity();
    }

    setLanguageMatching(matchingEnabled: boolean) {
        this.patchState(
            matchingEnabled,
            'entity',
            'targeting',
            'language',
            'matchingEnabled'
        );
        this.validateEntity();
    }

    setStartDate(startDate: Date) {
        this.patchState(startDate, 'entity', 'startDate');
        this.validateEntity();
    }

    setEndDate(endDate: Date) {
        this.patchState(endDate, 'entity', 'endDate');
        this.validateEntity();
    }

    setDeliveryType(deliveryType: DeliveryType) {
        this.patchState(deliveryType, 'entity', 'deliveryType');
        this.validateEntity();
    }

    setDayparting(dayparting: AdGroupDayparting) {
        this.patchState(dayparting, 'entity', 'dayparting');
        this.validateEntity();
    }

    setBiddingType(biddingType: BiddingType) {
        let bid = null;
        if (biddingType === BiddingType.CPC) {
            bid = this.state.extras.currentBids.cpc;
        } else {
            bid = this.state.extras.currentBids.cpm;
        }
        this.setState({
            ...this.state,
            entity: {
                ...this.state.entity,
                biddingType: biddingType,
                bid: bid,
            },
        });
        this.validateEntity();
    }

    setBid(bid: string) {
        this.patchState(bid, 'entity', 'bid');
        this.validateEntity();
    }

    setMaxBid(maxBid: string) {
        this.patchState(maxBid, 'entity', 'autopilot', 'maxBid');
        this.validateEntity();
    }

    setAutopilotDailyBudget(dailyBudget: string) {
        this.patchState(dailyBudget, 'entity', 'autopilot', 'dailyBudget');
        this.validateEntity();
    }

    setDailyClickCapping(clickCapping: string) {
        let clickCappingNumber = null;
        if (commonHelpers.isNotEmpty(clickCapping)) {
            clickCappingNumber = parseInt(clickCapping, 10) || null;
        }
        this.patchState(
            clickCappingNumber,
            'entity',
            'clickCappingDailyAdGroupMaxClicks'
        );
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

    isDeviceTargetingDifferentFromDefault(): boolean {
        const areTargetDevicesDifferent = !deepEqual(
            this.state.entity.targeting.devices,
            this.state.extras.defaultSettings.targetDevices
        );
        const areTargetOsDifferent = !deepEqual(
            this.state.entity.targeting.os,
            this.state.extras.defaultSettings.targetOs
        );
        const areTargetEnvironmentsDifferent = !deepEqual(
            this.state.entity.targeting.environments,
            this.state.extras.defaultSettings.targetEnvironments
        );

        return (
            areTargetDevicesDifferent ||
            areTargetOsDifferent ||
            areTargetEnvironmentsDifferent
        );
    }

    toggleTargetingDevice(device: string) {
        const oldDevices: string[] = this.state.entity.targeting.devices;
        const allDevices: string[] = TARGETING_DEVICE_OPTIONS.map(
            option => option.value
        );
        const newDevices: string[] = this.toggleTargetingItem(
            device,
            oldDevices,
            allDevices
        );

        this.patchState(newDevices, 'entity', 'targeting', 'devices');
        this.validateEntity();
    }

    toggleTargetingEnvironment(environment: string) {
        const oldEnvironments: string[] = this.state.entity.targeting
            .environments;
        const allEnvironments: string[] = TARGETING_ENVIRONMENT_OPTIONS.map(
            option => option.value
        );
        const newEnvironments: string[] = this.toggleTargetingItem(
            environment,
            oldEnvironments,
            allEnvironments
        );

        this.patchState(newEnvironments, 'entity', 'targeting', 'environments');
        this.validateEntity();
    }

    addDeviceTargetingOs(osName: string) {
        const newTargetOses: TargetOperatingSystem[] = this.state.entity.targeting.os.concat(
            {
                name: osName,
                version: {},
            }
        );
        this.patchState(newTargetOses, 'entity', 'targeting', 'os');
        this.validateEntity();
    }

    changeDeviceTargetingOs($event: ChangeEvent<TargetOperatingSystem>) {
        const newTargetOses: TargetOperatingSystem[] = this.patchListItem(
            this.state.entity.targeting.os,
            $event
        ).map(this.fixVersionOrder.bind(this));
        this.patchState(newTargetOses, 'entity', 'targeting', 'os');
        this.validateEntity();
    }

    deleteDeviceTargetingOs(deletedOs: TargetOperatingSystem) {
        const newTargetOses: TargetOperatingSystem[] = this.state.entity.targeting.os.filter(
            targetOs => targetOs.name !== deletedOs.name
        );
        this.patchState(newTargetOses, 'entity', 'targeting', 'os');
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

        this.patchState(
            newInterestTargeting,
            'entity',
            'targeting',
            'interest'
        );
        this.validateEntity();
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
        this.validateEntity();
    }

    setBluekaiTargeting(bluekaiTargeting: any) {
        this.patchState(bluekaiTargeting, 'entity', 'targeting', 'audience');
        this.validateEntity();
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
        this.validateEntity();
    }

    setManageRtbSourcesAsOne(manageRtbSourcesAsOne: boolean) {
        this.patchState(
            manageRtbSourcesAsOne,
            'entity',
            'manageRtbSourcesAsOne'
        );
        this.validateEntity();
    }

    setTrackingCode(trackingCode: string): void {
        this.patchState(trackingCode, 'entity', 'trackingCode');
        this.validateEntity();
    }

    addGeotargeting(geotargeting: Geotargeting): void {
        const geo = clone(this.state.entity.targeting.geo);
        const selectedLocations = clone(
            this.state.selectedGeotargetingLocations
        );

        const geotargetingTypeProperty = getIncludeExcludePropertyNameFromIncludeExcludeType(
            geotargeting.includeExcludeType
        );
        const locationTypeProperty = getGeotargetingLocationPropertyFromGeolocationType(
            geotargeting.selectedLocation.type
        );

        geo[geotargetingTypeProperty][locationTypeProperty].push(
            geotargeting.selectedLocation.key
        );
        selectedLocations.push(geotargeting.selectedLocation);

        this.setGeotargetingState(
            geo,
            selectedLocations,
            this.state.selectedZipTargetingLocation
        );
    }

    removeGeotargeting(geotargeting: Geotargeting): void {
        const geo = clone(this.state.entity.targeting.geo);
        const selectedLocations = clone(
            this.state.selectedGeotargetingLocations
        );

        const geotargetingTypeProperty = getIncludeExcludePropertyNameFromIncludeExcludeType(
            geotargeting.includeExcludeType
        );
        const locationTypeProperty = getGeotargetingLocationPropertyFromGeolocationType(
            geotargeting.selectedLocation.type
        );

        const geotargetingRemoveIndex = geo[geotargetingTypeProperty][
            locationTypeProperty
        ].findIndex((key: string) => key === geotargeting.selectedLocation.key);
        if (geotargetingRemoveIndex !== -1) {
            geo[geotargetingTypeProperty][locationTypeProperty].splice(
                geotargetingRemoveIndex,
                1
            );
        }

        const selectedLocationRemoveIndex = selectedLocations.findIndex(
            location => location.key === geotargeting.selectedLocation.key
        );
        if (selectedLocationRemoveIndex !== -1) {
            selectedLocations.splice(selectedLocationRemoveIndex, 1);
        }

        this.setGeotargetingState(
            geo,
            selectedLocations,
            this.state.selectedZipTargetingLocation
        );
    }

    setZipTargeting(zipTargeting: Geotargeting): void {
        if (!commonHelpers.isDefined(zipTargeting.zipCodes)) {
            return;
        }

        const geo = clone(this.state.entity.targeting.geo);
        if (zipTargeting.includeExcludeType === IncludeExcludeType.INCLUDE) {
            geo.included.postalCodes = zipTargeting.zipCodes;
            geo.excluded.postalCodes = [];
        } else {
            geo.excluded.postalCodes = zipTargeting.zipCodes;
            geo.included.postalCodes = [];
        }

        this.setGeotargetingState(
            geo,
            this.state.selectedGeotargetingLocations,
            zipTargeting.selectedLocation
        );
    }

    loadSelectedLocations(keys: string[]): void {
        if (isEmpty(keys)) {
            return;
        }

        const batches = [];
        const BATCH_SIZE = 50;
        for (let i = 0; i < keys.length; i += BATCH_SIZE) {
            batches.push(keys.slice(i, i + BATCH_SIZE));
        }

        const requestBatches = batches.map(batchKeys => {
            return this.locationService.list(
                null,
                null,
                batchKeys,
                BATCH_SIZE,
                null,
                () => {}
            );
        });

        this.executeParallelRequests(requestBatches).then(locations => {
            let selectedZipTargetingLocation: Geolocation = null;
            let selectedGeotargetingLocations: Geolocation[] = [];

            const postalCodes = this.state.entity.targeting.geo.included.postalCodes.concat(
                this.state.entity.targeting.geo.excluded.postalCodes
            );
            if (!isEmpty(postalCodes)) {
                const zipTargetingCountryKey = postalCodes[0].split(':')[0];
                selectedZipTargetingLocation = locations.find(
                    location => location.key === zipTargetingCountryKey
                );
                selectedGeotargetingLocations = locations.filter(
                    location => location.key !== zipTargetingCountryKey
                );
            } else {
                selectedGeotargetingLocations = locations;
            }

            this.setState({
                ...this.state,
                selectedZipTargetingLocation: selectedZipTargetingLocation,
                selectedGeotargetingLocations: selectedGeotargetingLocations,
            });
        });
    }

    searchLocations(searchParameters: GeolocationSearchParams): void {
        const requestsByType = searchParameters.types.map(type => {
            return this.locationService.list(
                searchParameters.nameContains,
                type,
                null,
                commonHelpers.getValueOrDefault(searchParameters.limit, 20),
                commonHelpers.getValueOrDefault(searchParameters.offset, 0),
                this.locationsRequestStateUpdater
            );
        });

        this.executeParallelRequests(requestsByType).then(locations => {
            this.patchState(locations, 'searchedLocations');
        });
    }

    clearSearchedLocations(): void {
        this.patchState([], 'searchedLocations');
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

        this.patchState(geoTargeting, 'entity', 'targeting', 'geo');
        this.validateEntity();
    }

    handleBidModifierImportFileChange(file: File): void {
        this.updateBidModifiersImportFile(file);
        this.validateBidModifiersFile();
    }

    updateBidModifiersImportFile(file: File): void {
        this.setState({
            ...this.state,
            bidModifiersImportFile: file,
            bidModifiersImportSummary: null,
            bidModifiersImportError: null,
        });
    }

    importBidModifiersFile(): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            if (!commonHelpers.isDefined(this.state.bidModifiersImportFile)) {
                resolve(false);
                return;
            }
            const adGroupId = commonHelpers.isDefined(this.state.entity.id)
                ? parseInt(this.state.entity.id, 10)
                : null;
            this.bidModifierService
                .importFromFile(
                    adGroupId,
                    null,
                    this.state.bidModifiersImportFile,
                    this.bidModifierRequestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (bidModifierUploadSummary: BidModifierUploadSummary) => {
                        this.patchState(
                            bidModifierUploadSummary,
                            'bidModifiersImportSummary'
                        );
                        resolve(true);
                    },
                    (errorResponse: HttpErrorResponse) => {
                        const bidModifiersImportError = storeHelpers.getStoreFieldsErrorsState(
                            new BidModifiersImportErrorState(),
                            errorResponse
                        );
                        this.patchState(
                            bidModifiersImportError,
                            'bidModifiersImportError'
                        );
                        resolve(false);
                    }
                );
        });
    }

    validateBidModifiersFile(): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            if (!commonHelpers.isDefined(this.state.bidModifiersImportFile)) {
                resolve(false);
                return;
            }
            const adGroupId = commonHelpers.isDefined(this.state.entity.id)
                ? parseInt(this.state.entity.id, 10)
                : null;
            this.bidModifierService
                .validateImportFile(
                    adGroupId,
                    null,
                    this.state.bidModifiersImportFile,
                    this.bidModifierRequestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (bidModifierUploadSummary: BidModifierUploadSummary) => {
                        this.patchState(
                            bidModifierUploadSummary,
                            'bidModifiersImportSummary'
                        );
                        resolve(true);
                    },
                    (errorResponse: HttpErrorResponse) => {
                        const bidModifiersImportError = storeHelpers.getStoreFieldsErrorsState(
                            new BidModifiersImportErrorState(),
                            errorResponse
                        );
                        this.patchState(
                            bidModifiersImportError,
                            'bidModifiersImportError'
                        );
                        resolve(false);
                    }
                );
        });
    }

    ngOnDestroy() {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    private isManageRtbSourcesAsOneChangeConfirmed(): boolean {
        if (
            !this.originalEntity ||
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

    /**
     * If the min version of the OS is newer than the max version, change the min version to match the max
     */
    private fixVersionOrder(
        targetOs: TargetOperatingSystem
    ): TargetOperatingSystem {
        const fixedTargetOs: TargetOperatingSystem = {...targetOs};
        const osType: OperatingSystem = OPERATING_SYSTEMS[fixedTargetOs.name];

        if (
            osType.versions &&
            fixedTargetOs.version &&
            fixedTargetOs.version.min &&
            fixedTargetOs.version.max
        ) {
            const osVersionNames: string[] = osType.versions.map(x => x.name);
            const indexOfMinVersion: number = osVersionNames.indexOf(
                fixedTargetOs.version.min
            );
            const indexOfMaxVersion: number = osVersionNames.indexOf(
                fixedTargetOs.version.max
            );
            if (indexOfMinVersion > indexOfMaxVersion) {
                fixedTargetOs.version.max = fixedTargetOs.version.min;
            }
        }

        return fixedTargetOs;
    }

    private patchListItem<T>(list: T[], $event: ChangeEvent<T>): T[] {
        const newList = list.map(item => {
            if (item === $event.target) {
                return {
                    ...$event.target,
                    ...$event.changes,
                };
            } else {
                return item;
            }
        });

        return newList;
    }

    private toggleTargetingItem<T>(item: T, oldItems: T[], allItems: T[]): T[] {
        let newItems: T[];
        if (oldItems.includes(item)) {
            newItems = oldItems.filter(x => x !== item);
        } else {
            newItems = oldItems.concat(item);
        }
        if (isEmpty(newItems)) {
            newItems = allItems;
        }
        return newItems;
    }

    private executeParallelRequests<T>(
        requests: Observable<T[]>[]
    ): Promise<T[]> {
        return new Promise<T[]>((resolve, reject) => {
            forkJoin(requests)
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (data: T[][]) => {
                        resolve([].concat(...data));
                    },
                    error => {
                        reject(error);
                    }
                );
        });
    }

    private setGeotargetingState(
        geo: IncludedExcluded<TargetRegions>,
        selectedGeotargetingLocations: Geolocation[],
        selectedZipTargetingLocation: Geolocation
    ) {
        this.setState({
            ...this.state,
            entity: {
                ...this.state.entity,
                targeting: {
                    ...this.state.entity.targeting,
                    geo: geo,
                },
            },
            selectedGeotargetingLocations: selectedGeotargetingLocations,
            selectedZipTargetingLocation: selectedZipTargetingLocation,
        });
        this.validateEntity();
    }
}
