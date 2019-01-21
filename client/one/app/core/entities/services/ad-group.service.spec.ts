import {asapScheduler, of} from 'rxjs';
import * as clone from 'clone';
import {AdGroupService} from './ad-group.service';
import {AdGroupEndpoint} from './ad-group.endpoint';
import {EntitiesUpdatesService} from './entities-updates.service';
import {AdGroup} from '../types/ad-group';
import {
    AdGroupState,
    EntityType,
    EntityUpdateAction,
} from '../../../app.constants';
import {tick, fakeAsync} from '@angular/core/testing';

describe('AdGroupService', () => {
    let service: AdGroupService;
    let adGroupEndpointStub: jasmine.SpyObj<AdGroupEndpoint>;
    let entitiesUpdatesServiceStub: jasmine.SpyObj<EntitiesUpdatesService>;
    let mockedAdGroup: AdGroup;

    beforeEach(() => {
        adGroupEndpointStub = jasmine.createSpyObj(AdGroupEndpoint.name, [
            'query',
            'create',
            'edit',
        ]);

        entitiesUpdatesServiceStub = jasmine.createSpyObj(
            EntitiesUpdatesService.name,
            ['registerEntityUpdate']
        );

        mockedAdGroup = {
            id: 12345,
            state: AdGroupState.ACTIVE,
            archived: false,
        };

        service = new AdGroupService(
            adGroupEndpointStub,
            entitiesUpdatesServiceStub
        );
    });

    it('should get the ad group via endpoint', () => {
        adGroupEndpointStub.query.and
            .returnValue(of(mockedAdGroup, asapScheduler))
            .calls.reset();

        service.get(mockedAdGroup.id).subscribe(adGroup => {
            expect(adGroup).toEqual(mockedAdGroup);
        });
        expect(adGroupEndpointStub.query).toHaveBeenCalledTimes(1);
        expect(adGroupEndpointStub.query).toHaveBeenCalledWith(
            mockedAdGroup.id
        );
    });

    it('should save new ad group and register entity update', fakeAsync(() => {
        adGroupEndpointStub.create.and
            .returnValue(of(mockedAdGroup, asapScheduler))
            .calls.reset();

        const mockedNewAdGroup = clone(mockedAdGroup);
        mockedNewAdGroup.id = null;
        service.save(mockedNewAdGroup).subscribe(adGroup => {
            expect(adGroup).toEqual(mockedAdGroup);
        });
        tick();

        expect(adGroupEndpointStub.create).toHaveBeenCalledTimes(1);
        expect(adGroupEndpointStub.create).toHaveBeenCalledWith(
            mockedNewAdGroup
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

        service.save(mockedAdGroup).subscribe(adGroup => {
            expect(adGroup).toEqual(mockedAdGroup);
        });
        tick();

        expect(adGroupEndpointStub.edit).toHaveBeenCalledTimes(1);
        expect(adGroupEndpointStub.edit).toHaveBeenCalledWith(mockedAdGroup);
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

        service.archive(mockedAdGroup.id).subscribe();
        tick();

        expect(adGroupEndpointStub.edit).toHaveBeenCalledTimes(1);
        expect(adGroupEndpointStub.edit).toHaveBeenCalledWith({
            id: mockedAdGroup.id,
            archived: true,
        });
        expect(
            entitiesUpdatesServiceStub.registerEntityUpdate
        ).toHaveBeenCalledWith({
            id: mockedAdGroup.id,
            type: EntityType.AD_GROUP,
            action: EntityUpdateAction.ARCHIVE,
        });
    }));
});
