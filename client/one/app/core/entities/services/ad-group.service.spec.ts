import {asapScheduler, of} from 'rxjs';
import * as clone from 'clone';
import {AdGroupService} from './ad-group.service';
import {AdGroupEndpoint} from './ad-group.endpoint';
import {EntitiesUpdatesService} from './entities-updates.service';
import {AdGroupWithExtras} from '../types/ad-group/ad-group-with-extras';
import {EntityType, EntityUpdateAction, Currency} from '../../../app.constants';
import {tick, fakeAsync} from '@angular/core/testing';
import {AdGroup} from '../types/ad-group/ad-group';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {AdGroupExtras} from '../types/ad-group/ad-group-extras';

describe('AdGroupService', () => {
    let service: AdGroupService;
    let adGroupEndpointStub: jasmine.SpyObj<AdGroupEndpoint>;
    let entitiesUpdatesServiceStub: jasmine.SpyObj<EntitiesUpdatesService>;
    let mockedAdGroupWithExtras: AdGroupWithExtras;
    let mockedAdGroup: AdGroup;
    let mockedAdGroupExtras: AdGroupExtras;
    let requestStateUpdater: RequestStateUpdater;

    beforeEach(() => {
        adGroupEndpointStub = jasmine.createSpyObj(AdGroupEndpoint.name, [
            'defaults',
            'get',
            'validate',
            'create',
            'edit',
        ]);

        entitiesUpdatesServiceStub = jasmine.createSpyObj(
            EntitiesUpdatesService.name,
            ['registerEntityUpdate']
        );

        mockedAdGroup = {
            id: 12345,
            campaignId: 12345,
            name: 'Test ad group',
        };

        mockedAdGroupExtras = {
            actionIsWaiting: false,
            canArchive: true,
            canRestore: false,
            isCampaignAutopilotEnabled: false,
            accountId: 12345,
            currency: Currency.USD,
            defaultSettings: {
                targetRegions: {
                    countries: [],
                    regions: [],
                    dma: [],
                    cities: [],
                    postalCodes: [],
                },
                exclusionTargetRegions: {
                    countries: [],
                    regions: [],
                    dma: [],
                    cities: [],
                    postalCodes: [],
                },
                targetDevices: [],
                targetOs: [],
                targetPlacements: [],
            },
            retargetableAdGroups: [],
            audiences: [],
            warnings: {},
            hacks: [],
        };

        mockedAdGroupWithExtras = {
            adGroup: mockedAdGroup,
            extras: mockedAdGroupExtras,
        };

        service = new AdGroupService(
            adGroupEndpointStub,
            entitiesUpdatesServiceStub
        );

        requestStateUpdater = (requestName, requestState) => {};
    });

    it('should get default ad group via endpoint', () => {
        const mockedNewAdGroupWithExtras = clone(mockedAdGroupWithExtras);
        mockedNewAdGroupWithExtras.adGroup.id = null;
        mockedNewAdGroupWithExtras.adGroup.name = 'New ad group';

        adGroupEndpointStub.defaults.and
            .returnValue(of(mockedNewAdGroupWithExtras, asapScheduler))
            .calls.reset();

        service
            .defaults(mockedAdGroup.campaignId, requestStateUpdater)
            .subscribe(adGroupWithExtras => {
                expect(adGroupWithExtras.adGroup).toEqual(
                    mockedNewAdGroupWithExtras.adGroup
                );
                expect(adGroupWithExtras.extras).toEqual(mockedAdGroupExtras);
            });
        expect(adGroupEndpointStub.defaults).toHaveBeenCalledTimes(1);
        expect(adGroupEndpointStub.defaults).toHaveBeenCalledWith(
            mockedAdGroup.campaignId,
            requestStateUpdater
        );
    });

    it('should get the ad group via endpoint', () => {
        adGroupEndpointStub.get.and
            .returnValue(of(mockedAdGroupWithExtras, asapScheduler))
            .calls.reset();

        service
            .get(mockedAdGroup.id, requestStateUpdater)
            .subscribe(adGroupWithExtras => {
                expect(adGroupWithExtras.adGroup).toEqual(mockedAdGroup);
                expect(adGroupWithExtras.extras).toEqual(mockedAdGroupExtras);
            });
        expect(adGroupEndpointStub.get).toHaveBeenCalledTimes(1);
        expect(adGroupEndpointStub.get).toHaveBeenCalledWith(
            mockedAdGroup.id,
            requestStateUpdater
        );
    });

    it('should save new ad group and register entity update', fakeAsync(() => {
        adGroupEndpointStub.create.and
            .returnValue(of(mockedAdGroup, asapScheduler))
            .calls.reset();

        const mockedNewAdGroup = clone(mockedAdGroup);
        mockedNewAdGroup.id = null;
        service
            .save(mockedNewAdGroup, requestStateUpdater)
            .subscribe(adGroup => {
                expect(adGroup).toEqual(mockedAdGroup);
            });
        tick();

        expect(adGroupEndpointStub.create).toHaveBeenCalledTimes(1);
        expect(adGroupEndpointStub.create).toHaveBeenCalledWith(
            mockedNewAdGroup,
            requestStateUpdater
        );
        expect(adGroupEndpointStub.edit).not.toHaveBeenCalled();
        expect(
            entitiesUpdatesServiceStub.registerEntityUpdate
        ).toHaveBeenCalledWith({
            id: mockedAdGroup.id,
            type: EntityType.AD_GROUP,
            action: EntityUpdateAction.CREATE,
        });
    }));

    it('should edit existing ad group and register entity update', fakeAsync(() => {
        adGroupEndpointStub.edit.and
            .returnValue(of(mockedAdGroup, asapScheduler))
            .calls.reset();

        service.save(mockedAdGroup, requestStateUpdater).subscribe(adGroup => {
            expect(adGroup).toEqual(mockedAdGroup);
        });
        tick();

        expect(adGroupEndpointStub.edit).toHaveBeenCalledTimes(1);
        expect(adGroupEndpointStub.edit).toHaveBeenCalledWith(
            mockedAdGroup,
            requestStateUpdater
        );
        expect(adGroupEndpointStub.create).not.toHaveBeenCalled();
        expect(
            entitiesUpdatesServiceStub.registerEntityUpdate
        ).toHaveBeenCalledWith({
            id: mockedAdGroup.id,
            type: EntityType.AD_GROUP,
            action: EntityUpdateAction.EDIT,
        });
    }));

    it('should archive an ad group and register entity update', fakeAsync(() => {
        adGroupEndpointStub.edit.and
            .returnValue(of({...mockedAdGroup, archived: true}, asapScheduler))
            .calls.reset();

        service.archive(mockedAdGroup.id, requestStateUpdater).subscribe();
        tick();

        expect(adGroupEndpointStub.edit).toHaveBeenCalledTimes(1);
        expect(adGroupEndpointStub.edit).toHaveBeenCalledWith(
            {
                id: mockedAdGroup.id,
                archived: true,
            },
            requestStateUpdater
        );
        expect(
            entitiesUpdatesServiceStub.registerEntityUpdate
        ).toHaveBeenCalledWith({
            id: mockedAdGroup.id,
            type: EntityType.AD_GROUP,
            action: EntityUpdateAction.ARCHIVE,
        });
    }));
});
