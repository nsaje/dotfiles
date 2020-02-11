import {of, asapScheduler, throwError} from 'rxjs';
import {tick, fakeAsync} from '@angular/core/testing';
import * as clone from 'clone';
import {AdGroupSettingsStore} from './ad-group-settings.store';
import {AdGroupService} from '../../../../core/entities/services/ad-group/ad-group.service';
import {AdGroupWithExtras} from '../../../../core/entities/types/ad-group/ad-group-with-extras';
import {AdGroup} from '../../../../core/entities/types/ad-group/ad-group';
import {AdGroupExtras} from '../../../../core/entities/types/ad-group/ad-group-extras';
import {AdGroupSettingsStoreFieldsErrorsState} from './ad-group-settings.store.fields-errors-state';
import {BidModifiersImportErrorState} from './bid-modifiers-import-error-state';
import {
    InterestCategory,
    AdGroupAutopilotState,
} from '../../../../app.constants';
import {DealsService} from '../../../../core/deals/services/deals.service';
import {Deal} from '../../../../core/deals/types/deal';
import {SourcesService} from '../../../../core/sources/services/sources.service';
import {Source} from '../../../../core/sources/types/source';
import {BidModifiersService} from '../../../../core/bid-modifiers/services/bid-modifiers.service';
import {BidModifierUploadSummary} from '../../../../core/bid-modifiers/types/bid-modifier-upload-summary';
import {TargetOperatingSystem} from '../../../../core/entities/types/common/target-operating-system';

describe('AdGroupSettingsStore', () => {
    let serviceStub: jasmine.SpyObj<AdGroupService>;
    let dealsServiceStub: jasmine.SpyObj<DealsService>;
    let sourcesServiceStub: jasmine.SpyObj<SourcesService>;
    let bidModifiersServiceStub: jasmine.SpyObj<BidModifiersService>;
    let store: AdGroupSettingsStore;
    let adGroupWithExtras: AdGroupWithExtras;
    let adGroup: AdGroup;
    let adGroupExtras: AdGroupExtras;
    let mockedSources: Source[];

    beforeEach(() => {
        serviceStub = jasmine.createSpyObj(AdGroupService.name, [
            'defaults',
            'get',
            'validate',
            'save',
            'archive',
        ]);
        dealsServiceStub = jasmine.createSpyObj(DealsService.name, ['list']);
        sourcesServiceStub = jasmine.createSpyObj(SourcesService.name, [
            'list',
        ]);
        bidModifiersServiceStub = jasmine.createSpyObj(
            BidModifiersService.name,
            ['save', 'importFromFile', 'validateImportFile']
        );

        store = new AdGroupSettingsStore(
            serviceStub,
            dealsServiceStub,
            sourcesServiceStub,
            bidModifiersServiceStub
        );
        adGroup = clone(store.state.entity);
        adGroupExtras = clone(store.state.extras);
        adGroupWithExtras = {
            adGroup: adGroup,
            extras: adGroupExtras,
        };
        mockedSources = [
            {slug: 'smaato', name: 'Smaato', released: true, deprecated: false},
        ];
    });

    it('should get default ad group via service', fakeAsync(() => {
        const mockedAdGroupWithExtras = clone(adGroupWithExtras);
        mockedAdGroupWithExtras.adGroup.name = 'New ad group';
        mockedAdGroupWithExtras.adGroup.campaignId = '12345';
        mockedAdGroupWithExtras.adGroup.startDate = new Date(2019, 0, 5);
        mockedAdGroupWithExtras.adGroup.endDate = new Date(2019, 1, 5);

        serviceStub.defaults.and
            .returnValue(of(mockedAdGroupWithExtras, asapScheduler))
            .calls.reset();

        sourcesServiceStub.list.and
            .returnValue(of(mockedSources, asapScheduler))
            .calls.reset();

        expect(store.state.entity).toEqual(adGroup);
        expect(store.state.extras).toEqual(adGroupExtras);
        expect(store.state.fieldsErrors).toEqual(
            new AdGroupSettingsStoreFieldsErrorsState()
        );

        store.loadEntityDefaults('12345');
        tick();

        expect(store.state.entity).toEqual(mockedAdGroupWithExtras.adGroup);
        expect(store.state.extras).toEqual(mockedAdGroupWithExtras.extras);
        expect(store.state.sources).toEqual(mockedSources);
        expect(store.state.fieldsErrors).toEqual(
            new AdGroupSettingsStoreFieldsErrorsState()
        );

        expect(serviceStub.defaults).toHaveBeenCalledTimes(1);
        expect(sourcesServiceStub.list).toHaveBeenCalledTimes(1);
    }));

    it('should get ad group via service', fakeAsync(() => {
        const mockedAdGroupWithExtras = clone(adGroupWithExtras);
        mockedAdGroupWithExtras.adGroup.id = '12345';
        mockedAdGroupWithExtras.adGroup.name = 'Test ad group 1';
        mockedAdGroupWithExtras.adGroup.campaignId = '12345';
        mockedAdGroupWithExtras.adGroup.startDate = new Date(2019, 0, 5);
        mockedAdGroupWithExtras.adGroup.endDate = new Date(2019, 1, 5);

        serviceStub.get.and
            .returnValue(of(mockedAdGroupWithExtras, asapScheduler))
            .calls.reset();

        sourcesServiceStub.list.and
            .returnValue(of(mockedSources, asapScheduler))
            .calls.reset();

        expect(store.state.entity).toEqual(adGroup);
        expect(store.state.extras).toEqual(adGroupExtras);
        expect(store.state.fieldsErrors).toEqual(
            new AdGroupSettingsStoreFieldsErrorsState()
        );

        store.loadEntity('12345');
        tick();

        expect(store.state.entity).toEqual(mockedAdGroupWithExtras.adGroup);
        expect(store.state.extras).toEqual(mockedAdGroupWithExtras.extras);
        expect(store.state.sources).toEqual(mockedSources);
        expect(store.state.fieldsErrors).toEqual(
            new AdGroupSettingsStoreFieldsErrorsState()
        );

        expect(serviceStub.get).toHaveBeenCalledTimes(1);
        expect(sourcesServiceStub.list).toHaveBeenCalledTimes(1);
    }));

    it('should correctly handle errors when validating ad group via service', fakeAsync(() => {
        const mockedAdGroupWithExtras = clone(adGroupWithExtras);
        mockedAdGroupWithExtras.adGroup.id = '12345';
        mockedAdGroupWithExtras.adGroup.campaignId = '12345';
        mockedAdGroupWithExtras.adGroup.startDate = new Date(2019, 0, 5);
        mockedAdGroupWithExtras.adGroup.endDate = new Date(2019, 1, 5);

        store.state.entity = mockedAdGroupWithExtras.adGroup;
        store.state.extras = mockedAdGroupWithExtras.extras;

        serviceStub.validate.and
            .returnValue(
                throwError({
                    message: 'Validation error',
                    error: {
                        details: {name: ['Please specify ad group name.']},
                    },
                })
            )
            .calls.reset();

        store.validateEntity();
        tick();

        expect(store.state.entity).toEqual(mockedAdGroupWithExtras.adGroup);
        expect(store.state.extras).toEqual(mockedAdGroupWithExtras.extras);
        expect(store.state.fieldsErrors).toEqual(
            jasmine.objectContaining({
                ...new AdGroupSettingsStoreFieldsErrorsState(),
                name: ['Please specify ad group name.'],
            })
        );

        expect(serviceStub.validate).toHaveBeenCalledTimes(1);

        serviceStub.validate.and
            .returnValue(of(null, asapScheduler))
            .calls.reset();

        store.validateEntity();
        tick();

        expect(store.state.entity).toEqual(mockedAdGroupWithExtras.adGroup);
        expect(store.state.extras).toEqual(mockedAdGroupWithExtras.extras);
        expect(store.state.fieldsErrors).toEqual(
            new AdGroupSettingsStoreFieldsErrorsState()
        );

        expect(serviceStub.validate).toHaveBeenCalledTimes(1);
    }));

    it('should successfully save ad group via service', fakeAsync(() => {
        const mockedAdGroupWithExtras = clone(adGroupWithExtras);
        mockedAdGroupWithExtras.adGroup.id = '12345';
        mockedAdGroupWithExtras.adGroup.name = 'Test ad group 1';
        mockedAdGroupWithExtras.adGroup.campaignId = '12345';
        serviceStub.get.and
            .returnValue(of(mockedAdGroupWithExtras, asapScheduler))
            .calls.reset();
        serviceStub.save.and
            .returnValue(of(mockedAdGroupWithExtras.adGroup, asapScheduler))
            .calls.reset();
        sourcesServiceStub.list.and
            .returnValue(of(mockedSources, asapScheduler))
            .calls.reset();

        store.loadEntity('12345');
        tick();

        store.saveEntity();
        tick();

        expect(store.state.entity).toEqual(mockedAdGroupWithExtras.adGroup);
        expect(store.state.sources).toEqual(mockedSources);
        expect(store.state.fieldsErrors).toEqual(
            new AdGroupSettingsStoreFieldsErrorsState()
        );
        expect(serviceStub.save).toHaveBeenCalledTimes(1);
        expect(sourcesServiceStub.list).toHaveBeenCalledTimes(1);
    }));

    it('should save ad group only if user confirmed the changes', fakeAsync(() => {
        const confirmSpy = spyOn(window, 'confirm');
        const mockedAdGroupWithExtras = clone(adGroupWithExtras);
        mockedAdGroupWithExtras.adGroup.manageRtbSourcesAsOne = true;
        serviceStub.get.and
            .returnValue(of(mockedAdGroupWithExtras, asapScheduler))
            .calls.reset();
        serviceStub.save.and
            .returnValue(
                of(
                    {
                        ...mockedAdGroupWithExtras.adGroup,
                        manageRtbSourcesAsOne: false,
                    },
                    asapScheduler
                )
            )
            .calls.reset();
        sourcesServiceStub.list.and
            .returnValue(of(mockedSources, asapScheduler))
            .calls.reset();

        store.loadEntity('12345');
        tick();

        store.patchState(false, 'entity', 'manageRtbSourcesAsOne');

        confirmSpy.and.returnValue(false);
        store.saveEntity();
        tick();
        expect(serviceStub.save).not.toHaveBeenCalled();

        confirmSpy.and.returnValue(true);
        store.saveEntity();
        tick();
        expect(serviceStub.save).toHaveBeenCalledTimes(1);
        expect(sourcesServiceStub.list).toHaveBeenCalledTimes(1);
    }));

    it('should correctly handle errors when saving ad group via service', fakeAsync(() => {
        const mockedAdGroupWithExtras = clone(adGroupWithExtras);
        mockedAdGroupWithExtras.adGroup.id = '12345';
        mockedAdGroupWithExtras.adGroup.campaignId = '12345';
        serviceStub.get.and
            .returnValue(of(mockedAdGroupWithExtras, asapScheduler))
            .calls.reset();
        serviceStub.save.and
            .returnValue(
                throwError({
                    message: 'Validation error',
                    error: {
                        details: {name: ['Please specify ad group name.']},
                    },
                })
            )
            .calls.reset();
        sourcesServiceStub.list.and
            .returnValue(of(mockedSources, asapScheduler))
            .calls.reset();

        store.loadEntity('12345');
        tick();

        store.saveEntity();
        tick();

        expect(store.state.entity).toEqual(mockedAdGroupWithExtras.adGroup);
        expect(store.state.sources).toEqual(mockedSources);
        expect(store.state.fieldsErrors).toEqual(
            jasmine.objectContaining({
                ...new AdGroupSettingsStoreFieldsErrorsState(),
                name: ['Please specify ad group name.'],
            })
        );
        expect(serviceStub.save).toHaveBeenCalledTimes(1);
        expect(sourcesServiceStub.list).toHaveBeenCalledTimes(1);
    }));

    it('should successfully archive ad group via service', async () => {
        const mockedAdGroup = clone(adGroup);
        mockedAdGroup.id = '12345';
        mockedAdGroup.name = 'Test ad group 1';
        mockedAdGroup.campaignId = '12345';
        mockedAdGroup.archived = false;

        store.state.entity = mockedAdGroup;

        const archivedAdGroup = clone(mockedAdGroup);
        archivedAdGroup.archived = true;
        serviceStub.archive.and
            .returnValue(of(archivedAdGroup, asapScheduler))
            .calls.reset();

        const shouldReload = await store.archiveEntity();

        expect(serviceStub.archive).toHaveBeenCalledTimes(1);
        expect(shouldReload).toBe(true);
    });

    it('should successfully handle errors when archiving ad group via service', async () => {
        const mockedAdGroup = clone(adGroup);
        mockedAdGroup.id = '12345';
        mockedAdGroup.name = 'Test ad group 1';
        mockedAdGroup.campaignId = '12345';
        mockedAdGroup.archived = false;

        store.state.entity = mockedAdGroup;

        serviceStub.archive.and
            .returnValue(
                throwError({
                    message: 'Internal server error',
                })
            )
            .calls.reset();

        const shouldReload = await store.archiveEntity();

        expect(serviceStub.archive).toHaveBeenCalledTimes(1);
        expect(shouldReload).toBe(false);
    });

    it('should correctly load available deals via deals service', fakeAsync(() => {
        const mockedKeyword = 'bla';
        const mockedAvailableDeals: Deal[] = [];

        dealsServiceStub.list.and
            .returnValue(of(mockedAvailableDeals, asapScheduler))
            .calls.reset();

        store.loadAvailableDeals(mockedKeyword);
        tick();

        expect(dealsServiceStub.list).toHaveBeenCalledTimes(1);
        expect(store.state.availableDeals).toEqual(mockedAvailableDeals);
    }));

    it('should correctly add deal', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        const mockedDeal = {
            id: '10000000',
            dealId: '45345',
            agencyId: '45',
            accountId: '55',
            description: 'test directDeal',
            name: 'test directDeal',
            source: 'urska',
            floorPrice: '0.0002',
            createdDt: new Date(),
            modifiedDt: new Date(),
            createdBy: 'test@test.com',
            numOfAccounts: 0,
            numOfCampaigns: 0,
            numOfAdgroups: 0,
        };
        store.addDeal(mockedDeal);

        expect(store.state.entity.deals).toEqual([mockedDeal]);
    });

    it('should correctly remove deal', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.state.entity.deals = [
            {
                id: '10000000',
                dealId: '45345',
                agencyId: '45',
                accountId: '55',
                description: 'test directDeal',
                name: 'test directDeal',
                source: 'urska',
                floorPrice: '0.0002',
                createdDt: new Date(),
                modifiedDt: new Date(),
                createdBy: 'test@test.com',
                numOfAccounts: 0,
                numOfCampaigns: 0,
                numOfAdgroups: 0,
            },
        ];

        store.removeDeal(store.state.entity.deals[0]);
        expect(store.state.entity.deals).toEqual([]);
    });

    it('should correctly determine if ad group settings have unsaved changes', fakeAsync(() => {
        serviceStub.get.and
            .returnValue(of(clone(adGroupWithExtras), asapScheduler))
            .calls.reset();
        sourcesServiceStub.list.and
            .returnValue(of(mockedSources, asapScheduler))
            .calls.reset();

        expect(store.doEntitySettingsHaveUnsavedChanges()).toBe(false);

        store.loadEntity('1');
        tick();
        expect(store.doEntitySettingsHaveUnsavedChanges()).toBe(false);

        store.setState({
            ...store.state,
            entity: {...store.state.entity, name: 'Modified name'},
        });
        expect(store.doEntitySettingsHaveUnsavedChanges()).toBe(true);
    }));

    it('should correctly change adgroup name', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.patchState('Generic name', 'entity', 'name');
        expect(store.state.entity.name).toEqual('Generic name');
        store.setName('Generic name 2');
        expect(store.state.entity.name).toEqual('Generic name 2');
    });

    it('should correctly determine if ad group autopilot is enabled', () => {
        store.patchState(
            AdGroupAutopilotState.ACTIVE_CPC_BUDGET,
            'entity',
            'autopilot',
            'state'
        );
        expect(store.isAdGroupAutopilotEnabled()).toBe(true);

        store.patchState(
            AdGroupAutopilotState.ACTIVE_CPC,
            'entity',
            'autopilot',
            'state'
        );
        expect(store.isAdGroupAutopilotEnabled()).toBe(false);
    });

    it('should correctly determine if ad group autopilot is enabled when campaign autopilot is enabled', () => {
        store.patchState(true, 'extras', 'isCampaignAutopilotEnabled');
        store.patchState(
            AdGroupAutopilotState.ACTIVE_CPC_BUDGET,
            'entity',
            'autopilot',
            'state'
        );
        expect(store.isAdGroupAutopilotEnabled()).toBe(false);
    });

    it('should correctly set device targeting', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();
        const $event: any = {
            targetDevices: ['TABLE', 'MOBILE'],
            targetPlacements: [],
            targetOs: ['MACOSX', 'LINUX'],
        };

        expect(store.state.entity.targeting.devices).toEqual([]);
        expect(store.state.entity.targeting.placements).toEqual([]);
        expect(store.state.entity.targeting.os).toEqual([]);
        expect(store.isDeviceTargetingDifferentFromDefault()).toEqual(false);
        store.setDeviceTargeting($event);
        expect(store.state.entity.targeting.devices).toEqual(
            $event.targetDevices
        );
        expect(store.state.entity.targeting.placements).toEqual(
            $event.targetPlacements
        );
        expect(store.state.entity.targeting.os).toEqual($event.targetOs);
        expect(store.isDeviceTargetingDifferentFromDefault()).toEqual(true);
    });

    it('should allow adding of device targeting', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.state.entity.targeting.devices = ['DESKTOP'];
        store.toggleTargetingDevice('MOBILE');
        expect(store.state.entity.targeting.devices).toEqual([
            'DESKTOP',
            'MOBILE',
        ]);
    });

    it('should allow deleting of device targeting', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.state.entity.targeting.devices = ['DESKTOP', 'MOBILE'];
        store.toggleTargetingDevice('DESKTOP');
        expect(store.state.entity.targeting.devices).toEqual(['MOBILE']);
    });

    it('should select all device targetings if all are deleted', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.state.entity.targeting.devices = ['DESKTOP'];
        store.toggleTargetingDevice('DESKTOP');
        expect(store.state.entity.targeting.devices).toEqual([
            'DESKTOP',
            'TABLET',
            'MOBILE',
        ]);
    });

    it('should allow adding of targeting placement', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.state.entity.targeting.placements = ['SITE'];
        store.toggleTargetingPlacement('APP');
        expect(store.state.entity.targeting.placements).toEqual([
            'SITE',
            'APP',
        ]);
    });

    it('should allow deleting of targeting placement', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.state.entity.targeting.placements = ['SITE', 'APP'];
        store.toggleTargetingPlacement('SITE');
        expect(store.state.entity.targeting.placements).toEqual(['APP']);
    });

    it('should select all targeting placements if all are deleted', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.state.entity.targeting.placements = ['SITE'];
        store.toggleTargetingPlacement('SITE');
        expect(store.state.entity.targeting.placements).toEqual([
            'SITE',
            'APP',
        ]);
    });

    it('should allow adding device targeting OSes', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();
        expect(store.state.entity.targeting.os).toEqual([]);
        expect(store.isDeviceTargetingDifferentFromDefault()).toEqual(false);
        store.addDeviceTargetingOs('WINDOWS');
        expect(store.state.entity.targeting.os).toEqual([
            {name: 'WINDOWS', version: {}},
        ]);
        expect(store.isDeviceTargetingDifferentFromDefault()).toEqual(true);
    });

    it('should allow updating device targeting OSes', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();
        const windows: TargetOperatingSystem = {
            name: 'WINDOWS',
            version: {min: 'WINDOWS_XP', max: 'WINDOWS_10'},
        };
        store.state.entity.targeting.os = [windows];

        store.changeDeviceTargetingOs({
            target: windows,
            changes: {version: {min: 'WINDOWS_XP', max: 'WINDOWS_7'}},
        });

        expect(store.state.entity.targeting.os).toEqual([
            {name: 'WINDOWS', version: {min: 'WINDOWS_XP', max: 'WINDOWS_7'}},
        ]);
    });

    it('should fix max OS version when the updated min OS version is set higher than the max', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();
        const windows: TargetOperatingSystem = {
            name: 'WINDOWS',
            version: {min: 'WINDOWS_XP', max: 'WINDOWS_10'},
        };
        store.state.entity.targeting.os = [windows];

        store.changeDeviceTargetingOs({
            target: windows,
            changes: {version: {min: 'WINDOWS_7', max: 'WINDOWS_XP'}},
        });

        expect(store.state.entity.targeting.os).toEqual([
            {name: 'WINDOWS', version: {min: 'WINDOWS_7', max: 'WINDOWS_7'}},
        ]);
    });

    it('should allow deleting device targeting OSes', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();
        const windows: TargetOperatingSystem = {
            name: 'WINDOWS',
            version: {min: 'WINDOWS_XP', max: 'WINDOWS_10'},
        };
        store.state.entity.targeting.os = [windows];

        store.deleteDeviceTargetingOs(windows);

        expect(store.state.entity.targeting.os).toEqual([]);
    });

    it('should correctly set publisher groups', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();
        const $event: any = {
            whitelistedPublisherGroups: [123, 456, 789],
            blacklistedPublisherGroups: [],
        };

        expect(store.state.entity.targeting.publisherGroups).toEqual({
            included: [],
            excluded: [],
        });

        store.setPublisherGroupsTargeting($event);

        expect(store.state.entity.targeting.publisherGroups).toEqual({
            included: $event.whitelistedPublisherGroups,
            excluded: $event.blacklistedPublisherGroups,
        });
    });

    it('should correctly set interests', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();
        const $event: any = {
            includedInterests: [
                InterestCategory.CAREER,
                InterestCategory.COMMUNICATION,
            ],
            excludedInterests: [InterestCategory.EDUCATION],
        };

        expect(store.state.entity.targeting.interest).toEqual({
            included: [],
            excluded: [],
        });

        store.setInterestTargeting($event);

        expect(store.state.entity.targeting.interest).toEqual({
            included: $event.includedInterests,
            excluded: $event.excludedInterests,
        });
    });

    it('should correctly set retargeting', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();
        const $event: any = {
            includedAudiences: [123, 456, 789],
            excludedAudiences: [555, 666],
            includedAdGroups: [222, 767, 898],
            excludedAdGroups: [454],
        };

        expect(store.state.entity.targeting.customAudiences).toEqual({
            included: [],
            excluded: [],
        });

        expect(store.state.entity.targeting.retargetingAdGroups).toEqual({
            included: [],
            excluded: [],
        });

        store.setRetargeting($event);

        expect(store.state.entity.targeting.customAudiences).toEqual({
            included: $event.includedAudiences,
            excluded: $event.excludedAudiences,
        });

        expect(store.state.entity.targeting.retargetingAdGroups).toEqual({
            included: $event.includedAdGroups,
            excluded: $event.excludedAdGroups,
        });
    });

    it('should correctly set bluekai', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();
        const $event: any = {
            and: [
                {or: [{category: 'bluekai: 123'}, {category: 'bluekai: 234'}]},
                {or: [{category: 'bluekai: 345'}]},
                {not: [{or: [{category: 'bluekai: 432'}]}]},
            ],
        };

        expect(store.state.entity.targeting.audience).toEqual({});
        store.setBluekaiTargeting($event);
        expect(store.state.entity.targeting.audience).toEqual($event);
    });

    it('should correctly set state when ad group optimization is set to inactive', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();
        store.patchState(true, 'entity', 'manageRtbSourcesAsOne');
        store.setAdGroupAutopilotState(AdGroupAutopilotState.INACTIVE);
        expect(store.state.entity.autopilot.state).toEqual(
            AdGroupAutopilotState.INACTIVE
        );
        expect(store.state.entity.manageRtbSourcesAsOne).toBe(true);
    });

    it('should correctly set state when ad group optimization is set to optimize towards campaign goal', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();
        store.patchState(false, 'entity', 'manageRtbSourcesAsOne');
        store.setAdGroupAutopilotState(AdGroupAutopilotState.ACTIVE_CPC_BUDGET);
        expect(store.state.entity.autopilot.state).toEqual(
            AdGroupAutopilotState.ACTIVE_CPC_BUDGET
        );
        expect(store.state.entity.manageRtbSourcesAsOne).toBe(true);
    });

    it('should correctly set trackingCode', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();
        const $event = 'New tracking code';

        expect(store.state.entity.trackingCode).toEqual(null);
        store.setTrackingCode($event);
        expect(store.state.entity.trackingCode).toEqual($event);
    });

    it('should correctly change click capping', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.patchState(22, 'entity', 'clickCappingDailyAdGroupMaxClicks');
        expect(store.state.entity.clickCappingDailyAdGroupMaxClicks).toEqual(
            22
        );
        store.setDailyClickCapping('30');
        expect(store.state.entity.clickCappingDailyAdGroupMaxClicks).toEqual(
            30
        );
    });

    it('should correctly change frequency capping', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.patchState(22, 'entity', 'frequencyCapping');
        expect(store.state.entity.frequencyCapping).toEqual(22);
        store.setFrequencyCapping('30');
        expect(store.state.entity.frequencyCapping).toEqual(30);
    });

    it('should correctly set location targeting', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();
        const $event: any = {
            includedLocations: {
                countries: [],
                regions: [],
                dma: [],
                cities: [],
                postalCodes: ['CO:123'],
            },
            excludedLocations: {
                countries: [],
                regions: [],
                dma: [],
                cities: [],
                postalCodes: ['CO:345'],
            },
        };

        expect(store.state.entity.targeting.geo.included).toEqual({
            countries: [],
            regions: [],
            dma: [],
            cities: [],
            postalCodes: [],
        });
        expect(store.state.entity.targeting.geo.excluded).toEqual({
            countries: [],
            regions: [],
            dma: [],
            cities: [],
            postalCodes: [],
        });
        expect(store.isLocationTargetingDifferentFromDefault()).toEqual(false);
        store.setLocationTargeting($event);
        expect(store.state.entity.targeting.geo.included).toEqual({
            countries: [],
            regions: [],
            dma: [],
            cities: [],
            postalCodes: ['CO:123'],
        });
        expect(store.state.entity.targeting.geo.excluded).toEqual({
            countries: [],
            regions: [],
            dma: [],
            cities: [],
            postalCodes: ['CO:345'],
        });
        expect(store.isLocationTargetingDifferentFromDefault()).toEqual(true);
    });

    it('should correctly reset bid modifiers import file import summary and error state', () => {
        const mockedBidModifierImportFile = {name: 'upload.csv'} as File;
        const mockedBidModifiersImportSummary = {} as BidModifierUploadSummary;
        const mockedBidModifiersImportError = new BidModifiersImportErrorState();
        store.setState({
            ...store.state,
            bidModifiersImportFile: mockedBidModifierImportFile,
            bidModifiersImportSummary: mockedBidModifiersImportSummary,
            bidModifiersImportError: mockedBidModifiersImportError,
        });

        store.updateBidModifiersImportFile(null);

        expect(store.state.bidModifiersImportFile).toEqual(null);
        expect(store.state.bidModifiersImportSummary).toEqual(null);
        expect(store.state.bidModifiersImportError).toEqual(null);
    });

    it('should correctly reset bid modifiers import summary and error state', () => {
        const mockedBidModifierImportFile = {name: 'upload.csv'} as File;
        const mockedBidModifiersImportSummary = {} as BidModifierUploadSummary;
        const mockedBidModifiersImportError = new BidModifiersImportErrorState();
        store.setState({
            ...store.state,
            bidModifiersImportFile: null,
            bidModifiersImportSummary: mockedBidModifiersImportSummary,
            bidModifiersImportError: mockedBidModifiersImportError,
        });

        store.updateBidModifiersImportFile(mockedBidModifierImportFile);

        expect(store.state.bidModifiersImportFile).toEqual(
            mockedBidModifierImportFile
        );
        expect(store.state.bidModifiersImportSummary).toEqual(null);
        expect(store.state.bidModifiersImportError).toEqual(null);
    });

    it('should correctly import bid modifiers file via bid modifier service', fakeAsync(() => {
        const mockedBidModifierImportFile = {name: 'upload.csv'} as File;
        const mockedBidModifierUploadSummariy: BidModifierUploadSummary = {
            deleted: {
                count: 0,
                dimensions: 0,
                summary: [],
            },
            created: {
                count: 0,
                dimensions: 0,
                summary: [],
            },
        };
        store.patchState('1', 'entity', 'id');
        store.patchState(mockedBidModifierImportFile, 'bidModifiersImportFile');

        bidModifiersServiceStub.importFromFile.and
            .returnValue(of(mockedBidModifierUploadSummariy, asapScheduler))
            .calls.reset();

        store.importBidModifiersFile();
        tick();

        expect(bidModifiersServiceStub.importFromFile).toHaveBeenCalledTimes(1);
        expect(
            bidModifiersServiceStub.importFromFile.calls.mostRecent().args[1]
        ).toEqual(null);
        expect(store.state.bidModifiersImportSummary).toEqual(
            mockedBidModifierUploadSummariy
        );
    }));

    it('should correctly handle error while importing bid modifiers file via bid modifier service', fakeAsync(() => {
        const mockedBidModifierImportFile = {name: 'upload.csv'} as File;
        store.patchState('1', 'entity', 'id');
        store.patchState(mockedBidModifierImportFile, 'bidModifiersImportFile');

        bidModifiersServiceStub.importFromFile.and
            .returnValue(
                throwError({
                    message: 'Validation error',
                    error: {
                        details: {
                            file: 'Errors in CSV file!',
                            errorFileUrl: 'abcdef',
                        },
                    },
                })
            )
            .calls.reset();

        store.importBidModifiersFile();
        tick();

        expect(bidModifiersServiceStub.importFromFile).toHaveBeenCalledTimes(1);
        expect(
            bidModifiersServiceStub.importFromFile.calls.mostRecent().args[1]
        ).toEqual(null);
        expect(store.state.bidModifiersImportError.errorFileUrl).toEqual(
            'abcdef'
        );
    }));

    it('should correctly validate bid modifiers import file via bid modifier service', fakeAsync(() => {
        const mockedBidModifierImportFile = {name: 'upload.csv'} as File;
        const mockedBidModifierUploadSummariy: BidModifierUploadSummary = {
            deleted: {
                count: 0,
                dimensions: 0,
                summary: [],
            },
            created: {
                count: 0,
                dimensions: 0,
                summary: [],
            },
        };
        store.patchState('1', 'entity', 'id');
        store.patchState(mockedBidModifierImportFile, 'bidModifiersImportFile');

        bidModifiersServiceStub.validateImportFile.and
            .returnValue(of(mockedBidModifierUploadSummariy, asapScheduler))
            .calls.reset();

        store.validateBidModifiersFile();
        tick();

        expect(
            bidModifiersServiceStub.validateImportFile
        ).toHaveBeenCalledTimes(1);
        expect(
            bidModifiersServiceStub.validateImportFile.calls.mostRecent()
                .args[1]
        ).toEqual(null);
        expect(store.state.bidModifiersImportSummary).toEqual(
            mockedBidModifierUploadSummariy
        );
    }));

    it('should correctly handle error while importing bid modifiers file via bid modifier service', fakeAsync(() => {
        const mockedBidModifierImportFile = {name: 'upload.csv'} as File;
        store.patchState('1', 'entity', 'id');
        store.patchState(mockedBidModifierImportFile, 'bidModifiersImportFile');

        bidModifiersServiceStub.validateImportFile.and
            .returnValue(
                throwError({
                    message: 'Validation error',
                    error: {
                        details: {
                            file: 'Errors in CSV file!',
                            errorFileUrl: 'abcdef',
                        },
                    },
                })
            )
            .calls.reset();

        store.validateBidModifiersFile();
        tick();

        expect(
            bidModifiersServiceStub.validateImportFile
        ).toHaveBeenCalledTimes(1);
        expect(
            bidModifiersServiceStub.validateImportFile.calls.mostRecent()
                .args[1]
        ).toEqual(null);
        expect(store.state.bidModifiersImportError.errorFileUrl).toEqual(
            'abcdef'
        );
    }));
});
