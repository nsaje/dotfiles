import {fakeAsync, tick} from '@angular/core/testing';
import {asapScheduler, of, noop} from 'rxjs';
import * as clone from 'clone';
import {DealsLibraryStore} from './deals-library.store';
import {SourcesService} from '../../../../core/sources/services/sources.service';
import {DealsService} from '../../../../core/deals/services/deals.service';
import {DealsLibraryStoreFieldsErrorsState} from './deals-library.store.fields-errors-state';
import {DealsLibraryStoreState} from './deals-library.store.state';
import {Deal} from '../../../../core/deals/types/deal';
import {Source} from '../../../../core/sources/types/source';
import {DealConnection} from '../../../../core/deals/types/deal-connection';
import {AccountService} from '../../../../core/entities/services/account/account.service';
import {Account} from '../../../../core/entities/types/account/account';
import * as mockHelpers from '../../../../testing/mock.helpers';
import {state} from '@angular/animations';
import {ScopeSelectorState} from '../../../../shared/components/scope-selector/scope-selector.constants';

describe('DealsLibraryStore', () => {
    let dealsServiceStub: jasmine.SpyObj<DealsService>;
    let sourcesServiceStub: jasmine.SpyObj<SourcesService>;
    let accountsServiceStub: jasmine.SpyObj<AccountService>;
    let zemPermissionsStub: any;
    let store: DealsLibraryStore;
    let mockedDeals: Deal[];
    let mockedSources: Source[];
    let mockedAgencyId: string;
    let mockedConnections: DealConnection[];
    let mockedAccountId: string;
    let mockedAccounts: Account[];

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
        accountsServiceStub = jasmine.createSpyObj(AccountService.name, [
            'list',
        ]);
        zemPermissionsStub = jasmine.createSpyObj('zemPermissions', [
            'hasAgencyScope',
        ]);
        store = new DealsLibraryStore(
            dealsServiceStub,
            sourcesServiceStub,
            accountsServiceStub,
            zemPermissionsStub
        );
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

        mockedAccounts = [mockHelpers.getMockedAccount()];
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

        accountsServiceStub.list.and
            .returnValue(of(mockedAccounts, asapScheduler))
            .calls.reset();
        store.setStore(
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
        expect(store.state.accounts).toEqual(mockedAccounts);
        expect(dealsServiceStub.list).toHaveBeenCalledTimes(1);
        expect(sourcesServiceStub.list).toHaveBeenCalledTimes(1);
        expect(accountsServiceStub.list).toHaveBeenCalledTimes(1);
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

    it('should correctly set existing agency deal to activeEntity', () => {
        const mockedDeal = clone(mockedDeals[0]);
        mockedDeal.agencyId = mockedAgencyId;
        mockedDeal.accountId = null;
        store.state.agencyId = mockedAgencyId;
        store.state.hasAgencyScope = true;

        const mockedEmptyDeal = new DealsLibraryStoreState().activeEntity
            .entity;
        store.setActiveEntity(mockedDeal);

        expect(store.state.activeEntity.entity).toEqual({
            ...mockedEmptyDeal,
            ...mockedDeal,
        });
        expect(store.state.activeEntity.scopeState).toEqual(
            ScopeSelectorState.AGENCY_SCOPE
        );
        expect(store.state.activeEntity.isReadOnly).toEqual(false);
    });

    it('should correctly set existing agencyt deal to activeEntity with read only', () => {
        const mockedDeal = clone(mockedDeals[0]);
        mockedDeal.agencyId = mockedAgencyId;
        mockedDeal.accountId = null;
        store.state.agencyId = mockedAgencyId;
        store.state.accountId = mockedAccountId;
        store.state.hasAgencyScope = false;

        const mockedEmptyDeal = new DealsLibraryStoreState().activeEntity
            .entity;
        store.setActiveEntity(mockedDeal);

        expect(store.state.activeEntity.entity).toEqual({
            ...mockedEmptyDeal,
            ...mockedDeal,
        });
        expect(store.state.activeEntity.scopeState).toEqual(
            ScopeSelectorState.AGENCY_SCOPE
        );
        expect(store.state.activeEntity.isReadOnly).toEqual(true);
    });

    it('should correctly set existing account deal to activeEntity', () => {
        const mockedDeal = clone(mockedDeals[0]);
        mockedDeal.agencyId = null;
        mockedDeal.accountId = mockedAccountId;
        store.state.agencyId = mockedAgencyId;
        store.state.accountId = mockedAccountId;
        store.state.hasAgencyScope = false;

        const mockedEmptyDeal = new DealsLibraryStoreState().activeEntity
            .entity;
        store.setActiveEntity(mockedDeal);

        expect(store.state.activeEntity.entity).toEqual({
            ...mockedEmptyDeal,
            ...mockedDeal,
        });
        expect(store.state.activeEntity.scopeState).toEqual(
            ScopeSelectorState.ACCOUNT_SCOPE
        );
        expect(store.state.activeEntity.isReadOnly).toEqual(false);
    });

    it('should correctly set new account deal to activeEntity', () => {
        store.state.agencyId = mockedAgencyId;
        store.state.accountId = mockedAccountId;
        store.state.hasAgencyScope = true;

        store.setActiveEntity({});

        expect(store.state.activeEntity.entity).toEqual({
            ...new DealsLibraryStoreState().activeEntity.entity,
            accountId: mockedAccountId,
        });
        expect(store.state.activeEntity.scopeState).toEqual(
            ScopeSelectorState.ACCOUNT_SCOPE
        );
    });

    it('should correctly set new agency deal to activeEntity', () => {
        store.state.agencyId = mockedAgencyId;
        store.state.accountId = null;
        store.state.hasAgencyScope = true;

        store.setActiveEntity({});

        expect(store.state.activeEntity.entity).toEqual({
            ...new DealsLibraryStoreState().activeEntity.entity,
            agencyId: mockedAgencyId,
        });
        expect(store.state.activeEntity.scopeState).toEqual(
            ScopeSelectorState.AGENCY_SCOPE
        );
    });

    it('should set account to activeEntity', () => {
        store.state.activeEntity.entity = clone(mockedDeals[0]);
        store.setActiveEntityAccount(mockedAccountId);

        expect(store.state.activeEntity.entity.accountId).toEqual(
            mockedAccountId
        );
    });

    it('should set activeEntity scope to account scope', () => {
        store.state.accounts = clone(mockedAccounts);
        store.state.activeEntity.entity = clone(mockedDeals[0]);
        store.state.activeEntity.scopeState = ScopeSelectorState.AGENCY_SCOPE;
        store.state.accountId = mockedAccountId;

        store.setActiveEntityScope(ScopeSelectorState.ACCOUNT_SCOPE);

        expect(store.state.activeEntity.entity.accountId).toEqual(
            mockedAccountId
        );
        expect(store.state.activeEntity.entity.agencyId).toEqual(null);
        expect(store.state.activeEntity.scopeState).toEqual(
            ScopeSelectorState.ACCOUNT_SCOPE
        );
    });

    it('should set activeEntity scope to agency scope', () => {
        store.state.activeEntity.entity = clone(mockedDeals[0]);
        store.state.activeEntity.entity.agencyId = null;
        store.state.activeEntity.entity.accountId = mockedAccountId;
        store.state.activeEntity.scopeState = ScopeSelectorState.ACCOUNT_SCOPE;
        store.state.agencyId = mockedAgencyId;

        store.setActiveEntityScope(ScopeSelectorState.AGENCY_SCOPE);

        expect(store.state.activeEntity.entity.agencyId).toEqual(
            mockedAgencyId
        );
        expect(store.state.activeEntity.entity.accountId).toEqual(null);
        expect(store.state.activeEntity.scopeState).toEqual(
            ScopeSelectorState.AGENCY_SCOPE
        );
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
