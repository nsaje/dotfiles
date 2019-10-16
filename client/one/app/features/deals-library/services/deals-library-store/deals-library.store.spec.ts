import {fakeAsync, tick} from '@angular/core/testing';
import {asapScheduler, of} from 'rxjs';
import * as clone from 'clone';
import {DealsLibraryStore} from './deals-library.store';
import {DealsService} from '../../../../core/deals/services/deals.service';
import {DealsLibraryStoreFieldsErrorsState} from './deals-library.store.fields-errors-state';
import {DealsLibraryStoreState} from './deals-library.store.state';
import {Deal} from '../../../../core/deals/types/deal';

describe('DealsLibraryStore', () => {
    let dealsServiceStub: jasmine.SpyObj<DealsService>;
    let store: DealsLibraryStore;
    let mockedDeals: Deal[];
    let mockedAgencyId: string;

    beforeEach(() => {
        dealsServiceStub = jasmine.createSpyObj(DealsService.name, [
            'list',
            'save',
            'validate',
            'get',
            'remove',
            'listConnections',
            'removeConnection',
        ]);
        store = new DealsLibraryStore(dealsServiceStub);
        mockedDeals = [
            {
                id: '10000000',
                dealId: '45345',
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
            {
                id: '10000001',
                dealId: '456346',
                description: 'second test deal',
                name: 'test deal number two',
                source: 'test2',
                floorPrice: '0.0007',
                createdDt: new Date(),
                modifiedDt: new Date(),
                createdBy: 'test@test.com',
                numOfAccounts: 0,
                numOfCampaigns: 0,
                numOfAdgroups: 0,
            },
            {
                id: '10000002',
                dealId: '345245',
                description: 'test 3',
                name: 'test deal 3',
                source: 'bsoutbrain',
                floorPrice: '0.0047',
                createdDt: new Date(),
                modifiedDt: new Date(),
                createdBy: 'test@test.com',
                numOfAccounts: 0,
                numOfCampaigns: 0,
                numOfAdgroups: 0,
            },
        ];
        mockedAgencyId = '71';
    });

    it('should list deals via service', fakeAsync(() => {
        const mockedOffset = 1;
        const mockedLimit = 10;
        dealsServiceStub.list.and
            .returnValue(of(mockedDeals, asapScheduler))
            .calls.reset();
        store.loadEntities(mockedAgencyId, mockedOffset, mockedLimit);
        tick();

        expect(store.state.entities).toEqual(mockedDeals);
        expect(dealsServiceStub.list).toHaveBeenCalledTimes(1);
    }));

    it('should validate deal', fakeAsync(() => {
        dealsServiceStub.validate.and
            .returnValue(of(null, asapScheduler))
            .calls.reset();
        store.validateActiveEntity(mockedAgencyId);
        tick();

        expect(store.state.activeEntity.fieldsErrors).toEqual(
            new DealsLibraryStoreFieldsErrorsState()
        );
        expect(dealsServiceStub.validate).toHaveBeenCalledTimes(1);
    }));

    it('should remove deal', fakeAsync(() => {
        dealsServiceStub.remove.and
            .returnValue(of(null, asapScheduler))
            .calls.reset();
        store.deleteActiveEntity(mockedAgencyId);
        tick();

        expect(store.state.activeEntity.entity).toEqual(
            new DealsLibraryStoreState().activeEntity.entity
        );
        expect(dealsServiceStub.remove).toHaveBeenCalledTimes(1);
    }));

    it('should set deal to activeEntity', () => {
        const mockedDeal = clone(mockedDeals[0]);
        store.setActiveEntity(mockedDeal);
        expect(store.state.activeEntity.entity).toEqual(mockedDeal);
    });
});