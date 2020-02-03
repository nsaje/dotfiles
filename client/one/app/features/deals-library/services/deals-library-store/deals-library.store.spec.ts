import {fakeAsync, tick} from '@angular/core/testing';
import {asapScheduler, of} from 'rxjs';
import * as clone from 'clone';
import {DealsLibraryStore} from './deals-library.store';
import {SourcesService} from '../../../../core/sources/services/sources.service';
import {DealsService} from '../../../../core/deals/services/deals.service';
import {DealsLibraryStoreFieldsErrorsState} from './deals-library.store.fields-errors-state';
import {DealsLibraryStoreState} from './deals-library.store.state';
import {Deal} from '../../../../core/deals/types/deal';
import {Source} from '../../../../core/sources/types/source';
import {DealConnection} from '../../../../core/deals/types/deal-connection';

describe('DealsLibraryStore', () => {
    let dealsServiceStub: jasmine.SpyObj<DealsService>;
    let sourcesServiceStub: jasmine.SpyObj<SourcesService>;
    let store: DealsLibraryStore;
    let mockedDeals: Deal[];
    let mockedSources: Source[];
    let mockedAgencyId: string;
    let mockedConnections: DealConnection[];
    let mockedAccountId: string;

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
        sourcesServiceStub = jasmine.createSpyObj(SourcesService.name, [
            'list',
        ]);
        store = new DealsLibraryStore(dealsServiceStub, sourcesServiceStub);
        mockedDeals = [
            {
                id: '10000000',
                dealId: '45345',
                agencyId: '71',
                accountId: null,
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
                agencyId: '71',
                accountId: null,
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
                agencyId: '71',
                accountId: null,
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
        mockedSources = [
            {
                slug: 'nastest2',
                name: 'nastest2',
                released: false,
                deprecated: false,
            },
            {slug: 'smaato', name: 'Smaato', released: true, deprecated: false},
            {
                slug: 'nastest3',
                name: 'nastest3',
                released: false,
                deprecated: false,
            },
        ];

        mockedConnections = [
            {
                id: '10000003',
                account: {},
                campaign: {},
                adgroup: {
                    id: '221391',
                    name: 'Blog Content [Mobile]',
                },
            },
            {
                id: '10000002',
                account: {},
                campaign: {
                    id: '215744',
                    name: 'New campaign',
                },
                adgroup: {},
            },
            {
                id: '10000001',
                account: {
                    id: '525',
                    name: 'Demo account',
                },
                campaign: {},
                adgroup: {},
            },
            {
                id: '10000000',
                account: {},
                campaign: {},
                adgroup: {},
            },
        ];

        mockedAgencyId = '71';
        mockedAccountId = '55';
    });

    it('should correctly initialize store', fakeAsync(() => {
        const mockedOffset = 1;
        const mockedLimit = 10;
        dealsServiceStub.list.and
            .returnValue(of(mockedDeals, asapScheduler))
            .calls.reset();
        sourcesServiceStub.list.and
            .returnValue(of(mockedSources, asapScheduler))
            .calls.reset();
        store.initStore(
            mockedAgencyId,
            mockedAccountId,
            mockedOffset,
            mockedLimit,
            null
        );
        tick();

        expect(store.state.entities).toEqual(mockedDeals);
        expect(store.state.accountId).toEqual(mockedAccountId);
        expect(store.state.sources).toEqual(mockedSources);
        expect(dealsServiceStub.list).toHaveBeenCalledTimes(1);
        expect(sourcesServiceStub.list).toHaveBeenCalledTimes(1);
    }));

    it('should list deals via service', fakeAsync(() => {
        const mockedOffset = 1;
        const mockedLimit = 10;
        dealsServiceStub.list.and
            .returnValue(of(mockedDeals, asapScheduler))
            .calls.reset();
        store.loadEntities(mockedOffset, mockedLimit);
        tick();

        expect(store.state.entities).toEqual(mockedDeals);
        expect(dealsServiceStub.list).toHaveBeenCalledTimes(1);
    }));

    it('should validate deal', fakeAsync(() => {
        dealsServiceStub.validate.and
            .returnValue(of(null, asapScheduler))
            .calls.reset();
        store.validateActiveEntity();
        tick();

        expect(store.state.activeEntity.fieldsErrors).toEqual(
            new DealsLibraryStoreFieldsErrorsState()
        );
        expect(dealsServiceStub.validate).toHaveBeenCalledTimes(1);
    }));

    it('should remove deal', fakeAsync(() => {
        const mockedDealId = mockedDeals[0].id;
        dealsServiceStub.remove.and
            .returnValue(of(null, asapScheduler))
            .calls.reset();
        store.deleteEntity(mockedDealId);
        tick();

        expect(dealsServiceStub.remove).toHaveBeenCalledTimes(1);
    }));

    it('should change active entity', fakeAsync(() => {
        const mockedDeal = clone(mockedDeals[0]);
        const change = {
            target: mockedDeal,
            changes: {
                id: '1',
            },
        };
        dealsServiceStub.validate.and
            .returnValue(of(null, asapScheduler))
            .calls.reset();
        store.changeActiveEntity(change);
        tick();

        expect(store.state.activeEntity.entity.id).toEqual('1');
        expect(dealsServiceStub.validate).toHaveBeenCalledTimes(1);
    }));

    it('should set deal to activeEntity', () => {
        const mockedDeal = clone(mockedDeals[0]);
        store.state.agencyId = mockedDeal.agencyId;
        const mockedEmptyDeal = new DealsLibraryStoreState().activeEntity
            .entity;
        store.setActiveEntity(mockedDeal);

        expect(store.state.activeEntity.entity).toEqual({
            ...mockedEmptyDeal,
            ...mockedDeal,
        });
    });

    it('should load active entity connections', fakeAsync(() => {
        const mockedDeal = clone(mockedDeals[0]);
        store.setActiveEntity(mockedDeal);

        dealsServiceStub.listConnections.and
            .returnValue(of(mockedConnections, asapScheduler))
            .calls.reset();
        store.loadActiveEntityConnections();
        tick();

        expect(dealsServiceStub.listConnections).toHaveBeenCalledTimes(1);
        expect(store.state.activeEntity.connections).toEqual(mockedConnections);
    }));

    it('should remove connection', fakeAsync(() => {
        dealsServiceStub.removeConnection.and
            .returnValue(of(null, asapScheduler))
            .calls.reset();
        store.deleteActiveEntityConnection(mockedConnections[0].id);
        tick();

        expect(dealsServiceStub.removeConnection).toHaveBeenCalledTimes(1);
    }));
});
