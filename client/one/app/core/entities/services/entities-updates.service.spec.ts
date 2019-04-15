import {EntitiesUpdatesService} from './entities-updates.service';
import {EntityType, EntityUpdateAction} from '../../../app.constants';
import {EntityUpdate} from '../types/entity-update';

describe('EntitiesUpdatesService', () => {
    let service: EntitiesUpdatesService;
    let mockedEntityUpdate: EntityUpdate;

    beforeEach(() => {
        mockedEntityUpdate = {
            id: '1',
            type: EntityType.AD_GROUP,
            action: EntityUpdateAction.EDIT,
        };

        service = new EntitiesUpdatesService();
    });

    it('should notify subscribers about entity update when entity update is registered', () => {
        service.getAllUpdates$().subscribe(entityUpdate => {
            expect(entityUpdate).toEqual(mockedEntityUpdate);
        });

        service.registerEntityUpdate(mockedEntityUpdate);
    });

    it("should filter updates when subscribing to specific entity's updates", () => {
        const callbackSpy = jasmine.createSpy('callbackSpy');

        service
            .getUpdatesOfEntity$(mockedEntityUpdate.id, mockedEntityUpdate.type)
            .subscribe(callbackSpy);

        service.registerEntityUpdate({...mockedEntityUpdate, id: '2'});
        expect(callbackSpy).not.toHaveBeenCalled();

        service.registerEntityUpdate({
            ...mockedEntityUpdate,
            type: EntityType.CAMPAIGN,
        });
        expect(callbackSpy).not.toHaveBeenCalled();

        service.registerEntityUpdate(mockedEntityUpdate);
        expect(callbackSpy).toHaveBeenCalledTimes(1);
        expect(callbackSpy).toHaveBeenCalledWith(mockedEntityUpdate);
    });
});
