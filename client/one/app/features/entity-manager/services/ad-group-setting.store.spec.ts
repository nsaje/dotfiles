import {of, asapScheduler, throwError} from 'rxjs';
import {tick, fakeAsync} from '@angular/core/testing';
import * as clone from 'clone';
import {AdGroupSettingsStore} from './ad-group-settings.store';
import {AdGroupService} from '../../../core/entities/services/ad-group.service';
import {AdGroupWithExtras} from '../../../core/entities/types/ad-group/ad-group-with-extras';
import {AdGroup} from '../../../core/entities/types/ad-group/ad-group';
import {AdGroupExtras} from '../../../core/entities/types/ad-group/ad-group-extras';
import {AdGroupSettingsStoreFieldsErrorsState} from './ad-group-settings.store.fields-errors-state';

describe('AdGroupSettingsStore', () => {
    let serviceStub: jasmine.SpyObj<AdGroupService>;
    let store: AdGroupSettingsStore;
    let navigationNewServiceStub: jasmine.SpyObj<any>;
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
        navigationNewServiceStub = jasmine.createSpyObj(
            'zemNavigationNewService',
            ['refreshState']
        );

        store = new AdGroupSettingsStore(serviceStub, navigationNewServiceStub);
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
        mockedAdGroupWithExtras.adGroup.campaignId = 12345;
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

        const campaignId = 12345;
        store.loadEntityDefaults(campaignId);
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
        mockedAdGroupWithExtras.adGroup.id = 12345;
        mockedAdGroupWithExtras.adGroup.name = 'Test ad group 1';
        mockedAdGroupWithExtras.adGroup.campaignId = 12345;
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

        const id = 12345;
        store.loadEntity(id);
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
        mockedAdGroupWithExtras.adGroup.id = 12345;
        mockedAdGroupWithExtras.adGroup.campaignId = 12345;
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
        const mockedAdGroup = clone(adGroup);
        mockedAdGroup.id = 12345;
        mockedAdGroup.name = 'Test ad group 1';
        mockedAdGroup.campaignId = 12345;

        store.state.entity = mockedAdGroup;

        serviceStub.save.and
            .returnValue(of(mockedAdGroup, asapScheduler))
            .calls.reset();

        store.saveEntity();
        tick();

        expect(store.state.entity).toEqual(mockedAdGroup);
        expect(store.state.fieldsErrors).toEqual(
            new AdGroupSettingsStoreFieldsErrorsState()
        );

        expect(serviceStub.save).toHaveBeenCalledTimes(1);
    }));

    it('should correctly handle errors when saving ad group via service', fakeAsync(() => {
        const mockedAdGroup = clone(adGroup);
        mockedAdGroup.id = 12345;
        mockedAdGroup.campaignId = 12345;

        store.state.entity = mockedAdGroup;

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

        store.saveEntity();
        tick();

        expect(store.state.entity).toEqual(mockedAdGroup);
        expect(store.state.fieldsErrors).toEqual(
            jasmine.objectContaining({
                ...new AdGroupSettingsStoreFieldsErrorsState(),
                name: ['Please specify ad group name.'],
            })
        );

        expect(serviceStub.save).toHaveBeenCalledTimes(1);
    }));

    it('should successfully archive ad group via service', fakeAsync(() => {
        const mockedAdGroup = clone(adGroup);
        mockedAdGroup.id = 12345;
        mockedAdGroup.name = 'Test ad group 1';
        mockedAdGroup.campaignId = 12345;
        mockedAdGroup.archived = false;

        store.state.entity = mockedAdGroup;

        const archivedAdGroup = clone(mockedAdGroup);
        archivedAdGroup.archived = true;
        serviceStub.archive.and
            .returnValue(of(archivedAdGroup, asapScheduler))
            .calls.reset();

        navigationNewServiceStub.refreshState.and
            .returnValue(null)
            .calls.reset();

        store.archiveEntity();
        tick();

        expect(serviceStub.archive).toHaveBeenCalledTimes(1);
        expect(navigationNewServiceStub.refreshState).toHaveBeenCalledTimes(1);
    }));

    it('should successfully handle errors when archiving ad group via service', fakeAsync(() => {
        const mockedAdGroup = clone(adGroup);
        mockedAdGroup.id = 12345;
        mockedAdGroup.name = 'Test ad group 1';
        mockedAdGroup.campaignId = 12345;
        mockedAdGroup.archived = false;

        store.state.entity = mockedAdGroup;

        serviceStub.archive.and
            .returnValue(
                throwError({
                    message: 'Internal server error',
                })
            )
            .calls.reset();

        navigationNewServiceStub.refreshState.and
            .returnValue(null)
            .calls.reset();

        store.archiveEntity();
        tick();

        expect(serviceStub.archive).toHaveBeenCalledTimes(1);
        expect(navigationNewServiceStub.refreshState).not.toHaveBeenCalled();
    }));

    it('should correctly set device targeting', () => {
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
});
