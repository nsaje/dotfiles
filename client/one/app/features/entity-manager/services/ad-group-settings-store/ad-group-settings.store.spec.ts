import {of, asapScheduler, throwError} from 'rxjs';
import {tick, fakeAsync} from '@angular/core/testing';
import * as clone from 'clone';
import {AdGroupSettingsStore} from './ad-group-settings.store';
import {AdGroupService} from '../../../../core/entities/services/ad-group/ad-group.service';
import {AdGroupWithExtras} from '../../../../core/entities/types/ad-group/ad-group-with-extras';
import {AdGroup} from '../../../../core/entities/types/ad-group/ad-group';
import {AdGroupExtras} from '../../../../core/entities/types/ad-group/ad-group-extras';
import {AdGroupSettingsStoreFieldsErrorsState} from './ad-group-settings.store.fields-errors-state';
import {
    InterestCategory,
    AdGroupAutopilotState,
} from '../../../../app.constants';

describe('AdGroupSettingsStore', () => {
    let serviceStub: jasmine.SpyObj<AdGroupService>;
    let store: AdGroupSettingsStore;
    let adGroupWithExtras: AdGroupWithExtras;
    let adGroup: AdGroup;
    let adGroupExtras: AdGroupExtras;

    beforeEach(() => {
        serviceStub = jasmine.createSpyObj(AdGroupService.name, [
            'defaults',
            'get',
            'validate',
            'save',
            'archive',
        ]);

        store = new AdGroupSettingsStore(serviceStub);
        adGroup = clone(store.state.entity);
        adGroupExtras = clone(store.state.extras);
        adGroupWithExtras = {
            adGroup: adGroup,
            extras: adGroupExtras,
        };
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

        expect(store.state.entity).toEqual(adGroup);
        expect(store.state.extras).toEqual(adGroupExtras);
        expect(store.state.fieldsErrors).toEqual(
            new AdGroupSettingsStoreFieldsErrorsState()
        );

        store.loadEntityDefaults('12345');
        tick();

        expect(store.state.entity).toEqual(mockedAdGroupWithExtras.adGroup);
        expect(store.state.extras).toEqual(mockedAdGroupWithExtras.extras);
        expect(store.state.fieldsErrors).toEqual(
            new AdGroupSettingsStoreFieldsErrorsState()
        );

        expect(serviceStub.defaults).toHaveBeenCalledTimes(1);
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

        expect(store.state.entity).toEqual(adGroup);
        expect(store.state.extras).toEqual(adGroupExtras);
        expect(store.state.fieldsErrors).toEqual(
            new AdGroupSettingsStoreFieldsErrorsState()
        );

        store.loadEntity('12345');
        tick();

        expect(store.state.entity).toEqual(mockedAdGroupWithExtras.adGroup);
        expect(store.state.extras).toEqual(mockedAdGroupWithExtras.extras);
        expect(store.state.fieldsErrors).toEqual(
            new AdGroupSettingsStoreFieldsErrorsState()
        );

        expect(serviceStub.get).toHaveBeenCalledTimes(1);
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

        store.loadEntity('12345');
        tick();

        store.saveEntity();
        tick();

        expect(store.state.entity).toEqual(mockedAdGroupWithExtras.adGroup);
        expect(store.state.fieldsErrors).toEqual(
            new AdGroupSettingsStoreFieldsErrorsState()
        );
        expect(serviceStub.save).toHaveBeenCalledTimes(1);
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

        store.loadEntity('12345');
        tick();

        store.saveEntity();
        tick();

        expect(store.state.entity).toEqual(mockedAdGroupWithExtras.adGroup);
        expect(store.state.fieldsErrors).toEqual(
            jasmine.objectContaining({
                ...new AdGroupSettingsStoreFieldsErrorsState(),
                name: ['Please specify ad group name.'],
            })
        );
        expect(serviceStub.save).toHaveBeenCalledTimes(1);
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

    it('should correctly determine if ad group settings have unsaved changes', fakeAsync(() => {
        serviceStub.get.and
            .returnValue(of(clone(adGroupWithExtras), asapScheduler))
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
});
