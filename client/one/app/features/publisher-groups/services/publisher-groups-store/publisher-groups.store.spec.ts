import {fakeAsync, tick} from '@angular/core/testing';
import {asapScheduler, of} from 'rxjs';
import {PublisherGroupsStore} from './publisher-groups.store';
import {PublisherGroupsService} from '../../../../core/publisher-groups/services/publisher-groups.service';
import {PublisherGroup} from '../../../../core/publisher-groups/types/publisher-group';
import {AccountService} from '../../../../core/entities/services/account/account.service';
import {Account} from '../../../../core/entities/types/account/account';
import * as mockHelpers from '../../../../testing/mock.helpers';
import * as clone from 'clone';
import {PublisherGroupsStoreState} from './publisher-groups.store.state';
import {ScopeSelectorState} from '../../../../shared/components/scope-selector/scope-selector.constants';
import {PublisherGroupConnection} from '../../../../core/publisher-groups/types/publisher-group-connection';
import {AuthStore} from '../../../../core/auth/services/auth.store';

describe('PublisherGroupsStore', () => {
    let publisherGroupsServiceStub: jasmine.SpyObj<PublisherGroupsService>;
    let accountsServiceStub: jasmine.SpyObj<AccountService>;
    let authStoreStub: jasmine.SpyObj<AuthStore>;
    let store: PublisherGroupsStore;
    let mockedPublisherGroups: PublisherGroup[];
    let mockedPublisherGroupConnection: PublisherGroupConnection;
    let mockedAgencyId: string;
    let mockedAccountId: string;
    let mockedAccounts: Account[];

    beforeEach(() => {
        publisherGroupsServiceStub = jasmine.createSpyObj(
            PublisherGroupsService.name,
            [
                'listImplicit',
                'listExplicit',
                'upload',
                'remove',
                'listConnections',
                'removeConnection',
            ]
        );
        accountsServiceStub = jasmine.createSpyObj(AccountService.name, [
            'list',
        ]);
        authStoreStub = jasmine.createSpyObj(AuthStore.name, [
            'hasAgencyScope',
        ]);

        store = new PublisherGroupsStore(
            publisherGroupsServiceStub,
            accountsServiceStub,
            authStoreStub
        );

        mockedPublisherGroups = [
            {
                id: '10000000',
                name: 'something.com',
                accountId: '525',
                agencyId: null,
                includeSubdomains: false,
                implicit: false,
                size: 3,
                modifiedDt: new Date(),
                createdDt: new Date(),
                type: 'Blacklist',
                level: 'Campaign',
                levelName: 'Test campaign',
                levelId: 123456,
                entries: undefined,
            },
            {
                id: '10000000',
                name: 'test-group.com',
                accountId: '525',
                agencyId: null,
                includeSubdomains: false,
                implicit: false,
                size: 2,
                modifiedDt: new Date(),
                createdDt: new Date(),
                type: null,
                level: null,
                levelName: '',
                levelId: null,
                entries: undefined,
            },
            {
                id: '10000001',
                name: 'hmm.si',
                accountId: '525',
                agencyId: null,
                includeSubdomains: false,
                implicit: false,
                size: 2,
                modifiedDt: new Date(),
                createdDt: new Date(),
                type: null,
                level: null,
                levelName: '',
                levelId: null,
                entries: undefined,
            },
        ];

        mockedPublisherGroupConnection = {
            id: 1,
            name: 'test1',
            location: 'agencyBlacklist',
        };

        mockedAgencyId = '10';
        mockedAccountId = '525';

        mockedAccounts = [mockHelpers.getMockedAccount()];
    });

    it('should correctly initialize store', fakeAsync(() => {
        publisherGroupsServiceStub.listImplicit.and
            .returnValue(of(mockedPublisherGroups, asapScheduler))
            .calls.reset();
        publisherGroupsServiceStub.listExplicit.and
            .returnValue(of(mockedPublisherGroups, asapScheduler))
            .calls.reset();
        accountsServiceStub.list.and
            .returnValue(of(mockedAccounts, asapScheduler))
            .calls.reset();

        store.setStore(
            mockedAgencyId,
            mockedAccountId,
            {type: 'server', page: 1, pageSize: 10},
            {type: 'server', page: 1, pageSize: 10}
        );
        tick();

        expect(store.state.explicitEntities).toEqual(mockedPublisherGroups);
        expect(store.state.agencyId).toEqual(mockedAgencyId);
        expect(store.state.accountId).toEqual(mockedAccountId);
        expect(store.state.accounts).toEqual(mockedAccounts);

        expect(publisherGroupsServiceStub.listImplicit).toHaveBeenCalledTimes(
            1
        );
        expect(publisherGroupsServiceStub.listExplicit).toHaveBeenCalledTimes(
            1
        );
        expect(accountsServiceStub.list).toHaveBeenCalledTimes(1);
    }));

    it('should only call listImplicit a second time if only implicit pagination has changed', fakeAsync(() => {
        publisherGroupsServiceStub.listImplicit.and
            .returnValue(of(mockedPublisherGroups, asapScheduler))
            .calls.reset();
        publisherGroupsServiceStub.listExplicit.and
            .returnValue(of(mockedPublisherGroups, asapScheduler))
            .calls.reset();
        accountsServiceStub.list.and
            .returnValue(of(mockedAccounts, asapScheduler))
            .calls.reset();

        store.setStore(
            mockedAgencyId,
            mockedAccountId,
            {type: 'server', page: 1, pageSize: 10},
            {type: 'server', page: 1, pageSize: 10}
        );

        tick();

        store.setStore(
            mockedAgencyId,
            mockedAccountId,
            {type: 'server', page: 1, pageSize: 10},
            {type: 'server', page: 2, pageSize: 10}
        );

        tick();

        expect(publisherGroupsServiceStub.listImplicit).toHaveBeenCalledTimes(
            2
        );
        expect(publisherGroupsServiceStub.listExplicit).toHaveBeenCalledTimes(
            1
        );
        expect(accountsServiceStub.list).toHaveBeenCalledTimes(1);
    }));

    it('should only call listExplicit a second time if only explicit pagination has changed', fakeAsync(() => {
        publisherGroupsServiceStub.listImplicit.and
            .returnValue(of(mockedPublisherGroups, asapScheduler))
            .calls.reset();
        publisherGroupsServiceStub.listExplicit.and
            .returnValue(of(mockedPublisherGroups, asapScheduler))
            .calls.reset();
        accountsServiceStub.list.and
            .returnValue(of(mockedAccounts, asapScheduler))
            .calls.reset();

        store.setStore(
            mockedAgencyId,
            mockedAccountId,
            {type: 'server', page: 1, pageSize: 10},
            {type: 'server', page: 1, pageSize: 10}
        );

        tick();

        store.setStore(
            mockedAgencyId,
            mockedAccountId,
            {type: 'server', page: 1, pageSize: 20},
            {type: 'server', page: 1, pageSize: 10}
        );

        tick();

        expect(publisherGroupsServiceStub.listImplicit).toHaveBeenCalledTimes(
            1
        );
        expect(publisherGroupsServiceStub.listExplicit).toHaveBeenCalledTimes(
            2
        );
        expect(accountsServiceStub.list).toHaveBeenCalledTimes(1);
    }));

    it('should list implicit publisher groups via service', fakeAsync(() => {
        publisherGroupsServiceStub.listImplicit.and
            .returnValue(of(mockedPublisherGroups, asapScheduler))
            .calls.reset();
        store.loadEntities(true, {type: 'server', page: 1, pageSize: 10});
        tick();

        expect(store.state.implicitEntities).toEqual(mockedPublisherGroups);
        expect(publisherGroupsServiceStub.listImplicit).toHaveBeenCalledTimes(
            1
        );
    }));

    it('should list explicit publisher groups via service', fakeAsync(() => {
        publisherGroupsServiceStub.listExplicit.and
            .returnValue(of(mockedPublisherGroups, asapScheduler))
            .calls.reset();
        store.loadEntities(false, {type: 'server', page: 1, pageSize: 10});
        tick();

        expect(store.state.explicitEntities).toEqual(mockedPublisherGroups);
        expect(publisherGroupsServiceStub.listExplicit).toHaveBeenCalledTimes(
            1
        );
    }));

    it('should upload publisher groups via service', fakeAsync(() => {
        publisherGroupsServiceStub.upload.and
            .returnValue(of(mockedPublisherGroups[0], asapScheduler))
            .calls.reset();

        store.setActiveEntity(mockedPublisherGroups[0]);
        store.saveActiveEntity();
        tick();

        expect(publisherGroupsServiceStub.upload).toHaveBeenCalledTimes(1);
        expect(publisherGroupsServiceStub.upload).toHaveBeenCalledWith(
            mockedPublisherGroups[0],
            (<any>store).requestStateUpdater
        );
    }));

    it('should remove publisher group via service', fakeAsync(() => {
        const mockedPublisherGroupId = mockedPublisherGroups[0].id;
        publisherGroupsServiceStub.remove.and
            .returnValue(of(null, asapScheduler))
            .calls.reset();
        store.deleteEntity(mockedPublisherGroupId);
        tick();

        expect(publisherGroupsServiceStub.remove).toHaveBeenCalledTimes(1);
        expect(publisherGroupsServiceStub.remove).toHaveBeenCalledWith(
            mockedPublisherGroups[0].id,
            (<any>store).requestStateUpdater
        );
    }));

    it('should correctly set existing agency publisher group to activeEntity', () => {
        const mockedPublisherGroup = clone(mockedPublisherGroups[0]);
        mockedPublisherGroup.agencyId = mockedAgencyId;
        mockedPublisherGroup.accountId = null;
        store.state.agencyId = mockedAgencyId;
        store.state.hasAgencyScope = true;

        const mockedEmptyPublisherGroup = new PublisherGroupsStoreState()
            .activeEntity.entity;
        store.setActiveEntity(mockedPublisherGroup);

        expect(store.state.activeEntity.entity).toEqual({
            ...mockedEmptyPublisherGroup,
            ...mockedPublisherGroup,
        });
        expect(store.state.activeEntity.scopeState).toEqual(
            ScopeSelectorState.AGENCY_SCOPE
        );
        expect(store.state.activeEntity.isReadOnly).toEqual(false);
    });

    it('should correctly set existing agency publisher group to activeEntity with read only', () => {
        const mockedPublisherGroup = clone(mockedPublisherGroups[0]);
        mockedPublisherGroup.agencyId = mockedAgencyId;
        mockedPublisherGroup.accountId = null;
        store.state.agencyId = mockedAgencyId;
        store.state.accountId = mockedAccountId;
        store.state.hasAgencyScope = false;

        const mockedEmptyPublisherGroup = new PublisherGroupsStoreState()
            .activeEntity.entity;
        store.setActiveEntity(mockedPublisherGroup);

        expect(store.state.activeEntity.entity).toEqual({
            ...mockedEmptyPublisherGroup,
            ...mockedPublisherGroup,
        });
        expect(store.state.activeEntity.scopeState).toEqual(
            ScopeSelectorState.AGENCY_SCOPE
        );
        expect(store.state.activeEntity.isReadOnly).toEqual(true);
    });

    it('should correctly set existing account publisher group to activeEntity', () => {
        const mockedPublisherGroup = clone(mockedPublisherGroups[0]);
        mockedPublisherGroup.agencyId = null;
        mockedPublisherGroup.accountId = mockedAccountId;
        store.state.agencyId = mockedAgencyId;
        store.state.accountId = mockedAccountId;
        store.state.hasAgencyScope = false;

        const mockedEmptyPublisherGroup = new PublisherGroupsStoreState()
            .activeEntity.entity;
        store.setActiveEntity(mockedPublisherGroup);

        expect(store.state.activeEntity.entity).toEqual({
            ...mockedEmptyPublisherGroup,
            ...mockedPublisherGroup,
        });
        expect(store.state.activeEntity.scopeState).toEqual(
            ScopeSelectorState.ACCOUNT_SCOPE
        );
        expect(store.state.activeEntity.isReadOnly).toEqual(false);
    });

    it('should correctly set new account publisher group to activeEntity', () => {
        store.state.agencyId = mockedAgencyId;
        store.state.accountId = mockedAccountId;
        store.state.hasAgencyScope = true;

        store.setActiveEntity({});

        expect(store.state.activeEntity.entity).toEqual({
            ...new PublisherGroupsStoreState().activeEntity.entity,
            accountId: mockedAccountId,
        });
        expect(store.state.activeEntity.scopeState).toEqual(
            ScopeSelectorState.ACCOUNT_SCOPE
        );
    });

    it('should correctly set new agency publisher group to activeEntity', () => {
        store.state.agencyId = mockedAgencyId;
        store.state.accountId = null;
        store.state.hasAgencyScope = true;

        store.setActiveEntity({});

        expect(store.state.activeEntity.entity).toEqual({
            ...new PublisherGroupsStoreState().activeEntity.entity,
            agencyId: mockedAgencyId,
        });
        expect(store.state.activeEntity.scopeState).toEqual(
            ScopeSelectorState.AGENCY_SCOPE
        );
    });

    it('should set account to activeEntity', () => {
        store.state.activeEntity.entity = clone(mockedPublisherGroups[0]);

        store.setActiveEntityAccount(mockedAccountId);

        expect(store.state.activeEntity.entity.accountId).toEqual(
            mockedAccountId
        );
    });

    it('should set activeEntity scope to account scope', () => {
        store.state.accounts = clone(mockedAccounts);
        store.state.activeEntity.entity = clone(mockedPublisherGroups[0]);
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
        store.state.activeEntity.entity = clone(mockedPublisherGroups[0]);
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

    it('should list publisher group connections via service', fakeAsync(() => {
        const mockedPublisherGroup = clone(mockedPublisherGroups[0]);

        publisherGroupsServiceStub.listConnections.and
            .returnValue(of(null, asapScheduler))
            .calls.reset();
        store.setActiveEntity(mockedPublisherGroup);
        store.loadActiveEntityConnections();
        tick();

        expect(
            publisherGroupsServiceStub.listConnections
        ).toHaveBeenCalledTimes(1);
        expect(publisherGroupsServiceStub.listConnections).toHaveBeenCalledWith(
            mockedPublisherGroup.id,
            (<any>store).requestStateUpdater
        );
    }));

    it('should remove publisher group connection via service', fakeAsync(() => {
        const mockedPublisherGroup = clone(mockedPublisherGroups[0]);

        publisherGroupsServiceStub.removeConnection.and
            .returnValue(of(null, asapScheduler))
            .calls.reset();
        store.setActiveEntity(mockedPublisherGroup);
        store.deleteActiveEntityConnection(mockedPublisherGroupConnection);
        tick();

        expect(
            publisherGroupsServiceStub.removeConnection
        ).toHaveBeenCalledTimes(1);
        expect(
            publisherGroupsServiceStub.removeConnection
        ).toHaveBeenCalledWith(
            mockedPublisherGroup.id,
            mockedPublisherGroupConnection,
            (<any>store).requestStateUpdater
        );
    }));
});
