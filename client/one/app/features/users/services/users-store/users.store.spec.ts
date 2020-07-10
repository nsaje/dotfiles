import {fakeAsync, tick} from '@angular/core/testing';
import {asapScheduler, of} from 'rxjs';
import {UsersStore} from './users.store';
import {UsersService} from '../../../../core/users/services/users.service';
import {User} from '../../../../core/users/types/user';
import {AccountService} from '../../../../core/entities/services/account/account.service';
import {Account} from '../../../../core/entities/types/account/account';
import * as mockHelpers from '../../../../testing/mock.helpers';
import {UsersStoreState} from './users.store.state';
import {ScopeSelectorState} from '../../../../shared/components/scope-selector/scope-selector.constants';
import * as clone from 'clone';

describe('UsersStore', () => {
    let usersServiceStub: jasmine.SpyObj<UsersService>;
    let accountsServiceStub: jasmine.SpyObj<AccountService>;
    let zemPermissionsStub: any;
    let store: UsersStore;
    let mockedAccountUser: User;
    let mockedAgencyUser: User;
    let mockedInternalUser: User;
    let mockedUsers: User[];
    let mockedAgencyId: string;
    let mockedAccountId: string;
    let anotherMockedAccountId: string;
    let aThirdMockedAccountId: string;
    let mockedAccounts: Account[];
    let mockedInitialState: UsersStoreState;

    beforeEach(() => {
        usersServiceStub = jasmine.createSpyObj(UsersService.name, [
            'list',
            'create',
            'edit',
            'validate',
            'get',
            'remove',
        ]);
        accountsServiceStub = jasmine.createSpyObj(AccountService.name, [
            'list',
        ]);
        zemPermissionsStub = jasmine.createSpyObj('zemPermissions', [
            'canEditUsersOnAgency',
            'canEditUsersOnAllAccounts',
        ]);

        store = new UsersStore(
            usersServiceStub,
            accountsServiceStub,
            zemPermissionsStub
        );

        mockedAgencyId = '10';
        mockedAccountId = '515';
        anotherMockedAccountId = '525';
        aThirdMockedAccountId = '535';

        mockedAccountUser = {
            id: '10000001',
            email: 'account.user@outbrain.com',
            firstName: 'Account',
            lastName: 'User',
            entityPermissions: [
                {
                    accountId: mockedAccountId,
                    permission: 'read',
                },
                {
                    accountId: mockedAccountId,
                    permission: 'write',
                },
                {
                    accountId: mockedAccountId,
                    permission: 'user',
                },
                {
                    accountId: anotherMockedAccountId,
                    permission: 'read',
                },
                {
                    accountId: anotherMockedAccountId,
                    permission: 'write',
                },
                {
                    accountId: anotherMockedAccountId,
                    permission: 'budget',
                },
            ],
        };

        mockedAgencyUser = {
            id: '10000002',
            email: 'agency.user@outbrain.com',
            firstName: 'Agency',
            lastName: 'User',
            entityPermissions: [
                {
                    agencyId: mockedAgencyId,
                    permission: 'read',
                },
                {
                    agencyId: mockedAgencyId,
                    permission: 'write',
                },
            ],
        };

        mockedInternalUser = {
            id: '10000003',
            email: 'internal.user@outbrain.com',
            firstName: 'Internal',
            lastName: 'User',
            entityPermissions: [
                {
                    permission: 'read',
                },
                {
                    permission: 'agency_spend_margin',
                },
            ],
        };
        mockedUsers = [mockedAccountUser, mockedAgencyUser, mockedInternalUser];

        mockedAccounts = [
            {
                ...mockHelpers.getMockedAccount(),
                id: mockedAccountId,
            },
            {
                ...mockHelpers.getMockedAccount(),
                id: anotherMockedAccountId,
            },
            {
                ...mockHelpers.getMockedAccount(),
                id: aThirdMockedAccountId,
            },
        ];

        mockedInitialState = {
            ...new UsersStoreState(),
            agencyId: mockedAgencyId,
            accountId: mockedAccountId,
            hasAgencyScope: true,
            hasAllAccountsScope: true,
            entities: mockedUsers,
            accounts: mockedAccounts,
        };

        usersServiceStub.validate.and
            .returnValue(of(null, asapScheduler))
            .calls.reset();
        usersServiceStub.list.and
            .returnValue(of(mockedUsers, asapScheduler))
            .calls.reset();
        accountsServiceStub.list.and
            .returnValue(of(mockedAccounts, asapScheduler))
            .calls.reset();
        zemPermissionsStub.canEditUsersOnAgency.and
            .returnValue(true)
            .calls.reset();
        zemPermissionsStub.canEditUsersOnAllAccounts.and
            .returnValue(true)
            .calls.reset();
    });

    it('should correctly initialize store', fakeAsync(() => {
        store.setStore(mockedAgencyId, mockedAccountId, 1, 10, '', true);
        tick();

        expect(store.state.agencyId).toEqual(mockedAgencyId);
        expect(store.state.accountId).toEqual(mockedAccountId);
        expect(store.state.hasAgencyScope).toEqual(true);
        expect(store.state.hasAllAccountsScope).toEqual(true);
        expect(store.state.entities).toEqual(mockedUsers);
        expect(store.state.accounts).toEqual(mockedAccounts);

        expect(usersServiceStub.list).toHaveBeenCalledTimes(1);
        expect(accountsServiceStub.list).toHaveBeenCalledTimes(1);
    }));

    it('should change active entity', fakeAsync(() => {
        store.setState(mockedInitialState);

        const mockedUser = clone(mockedUsers[0]);
        const change = {
            target: mockedUser,
            changes: {
                firstName: 'Eric',
                lastName: 'Cartman',
            },
        };
        usersServiceStub.validate.and
            .returnValue(of(null, asapScheduler))
            .calls.reset();
        store.changeActiveEntity(change);
        tick();

        expect(store.state.activeEntity.entity.firstName).toEqual('Eric');
        expect(store.state.activeEntity.entity.lastName).toEqual('Cartman');
        expect(usersServiceStub.validate).toHaveBeenCalledTimes(1);
    }));

    it('should update user via service', fakeAsync(() => {
        store.setState(mockedInitialState);

        usersServiceStub.edit.and
            .returnValue(of(mockedUsers[0], asapScheduler))
            .calls.reset();

        store.setActiveEntity(mockedUsers[0]);
        store.saveActiveEntity();
        tick();

        expect(usersServiceStub.edit).toHaveBeenCalledTimes(1);
        expect(usersServiceStub.edit).toHaveBeenCalledWith(
            mockedUsers[0],
            mockedAgencyId,
            mockedAccountId,
            (<any>store).requestStateUpdater
        );
    }));

    it('should create user via service', fakeAsync(() => {
        store.setState(mockedInitialState);

        const newUser: User = {...mockedUsers[0], id: undefined};

        usersServiceStub.create.and
            .returnValue(of([mockedUsers[0]], asapScheduler))
            .calls.reset();

        store.setActiveEntity(newUser);
        store.saveActiveEntity();
        tick();

        expect(usersServiceStub.create).toHaveBeenCalledTimes(1);
        expect(usersServiceStub.create).toHaveBeenCalledWith(
            [newUser],
            mockedAgencyId,
            mockedAccountId,
            (<any>store).requestStateUpdater
        );
    }));

    it('should create multiple users via service', fakeAsync(() => {
        store.setState(mockedInitialState);

        const multiUser: User = {
            email:
                ' user1@outbrain.com,user2@outbrain.com, user3@outbrain.com , user4@outbrain.com ',
            entityPermissions: [
                {
                    permission: 'read',
                },
                {
                    permission: 'write',
                },
            ],
        };
        const expectedUsers: User[] = [
            {
                id: null,
                email: 'user1@outbrain.com',
                firstName: '',
                lastName: '',
                entityPermissions: [
                    {
                        permission: 'read',
                    },
                    {
                        permission: 'write',
                    },
                ],
            },
            {
                id: null,
                email: 'user2@outbrain.com',
                firstName: '',
                lastName: '',
                entityPermissions: [
                    {
                        permission: 'read',
                    },
                    {
                        permission: 'write',
                    },
                ],
            },
            {
                id: null,
                email: 'user3@outbrain.com',
                firstName: '',
                lastName: '',
                entityPermissions: [
                    {
                        permission: 'read',
                    },
                    {
                        permission: 'write',
                    },
                ],
            },
            {
                id: null,
                email: 'user4@outbrain.com',
                firstName: '',
                lastName: '',
                entityPermissions: [
                    {
                        permission: 'read',
                    },
                    {
                        permission: 'write',
                    },
                ],
            },
        ];
        usersServiceStub.create.and
            .returnValue(of(expectedUsers, asapScheduler))
            .calls.reset();

        store.setActiveEntity(multiUser);
        store.saveActiveEntity();
        tick();

        expect(usersServiceStub.create).toHaveBeenCalledTimes(1);
        expect(usersServiceStub.create).toHaveBeenCalledWith(
            expectedUsers,
            mockedAgencyId,
            mockedAccountId,
            (<any>store).requestStateUpdater
        );
    }));

    it('should remove user via service', fakeAsync(() => {
        store.setState(mockedInitialState);

        const mockedUserId = mockedUsers[0].id;
        usersServiceStub.remove.and
            .returnValue(of(null, asapScheduler))
            .calls.reset();
        store.deleteEntity(mockedUserId);
        tick();

        expect(usersServiceStub.remove).toHaveBeenCalledTimes(1);
        expect(usersServiceStub.remove).toHaveBeenCalledWith(
            mockedUsers[0].id,
            mockedAgencyId,
            mockedAccountId,
            (<any>store).requestStateUpdater
        );
    }));

    it("should correctly set selected user's basic info", fakeAsync(() => {
        store.setState(mockedInitialState);

        mockedUsers.forEach(user => {
            store.setActiveEntity(user);

            expect(store.state.activeEntity.entity.id).toEqual(user.id);
            expect(store.state.activeEntity.entity.email).toEqual(user.email);
            expect(store.state.activeEntity.entity.firstName).toEqual(
                user.firstName
            );
            expect(store.state.activeEntity.entity.lastName).toEqual(
                user.lastName
            );
            expect(store.state.activeEntity.entity.entityPermissions).toEqual(
                user.entityPermissions
            );
        });
    }));

    it('should correctly set readonly status', fakeAsync(() => {
        store.setState(mockedInitialState); // App user is internal user

        store.setActiveEntity(mockedAccountUser);
        expect(store.state.activeEntity.isReadOnly).toEqual(false);
        store.setActiveEntity(mockedAgencyUser);
        expect(store.state.activeEntity.isReadOnly).toEqual(false);
        store.setActiveEntity(mockedInternalUser);
        expect(store.state.activeEntity.isReadOnly).toEqual(false);

        store.setState({
            ...mockedInitialState,
            hasAllAccountsScope: false,
        }); // App user is agency manager

        store.setActiveEntity(mockedAccountUser);
        expect(store.state.activeEntity.isReadOnly).toEqual(false);
        store.setActiveEntity(mockedAgencyUser);
        expect(store.state.activeEntity.isReadOnly).toEqual(false);
        store.setActiveEntity(mockedInternalUser);
        expect(store.state.activeEntity.isReadOnly).toEqual(true);

        store.setState({
            ...mockedInitialState,
            hasAllAccountsScope: false,
            hasAgencyScope: false,
        }); // App user is account manager

        store.setActiveEntity(mockedAccountUser);
        expect(store.state.activeEntity.isReadOnly).toEqual(false);
        store.setActiveEntity(mockedAgencyUser);
        expect(store.state.activeEntity.isReadOnly).toEqual(true);
        store.setActiveEntity(mockedInternalUser);
        expect(store.state.activeEntity.isReadOnly).toEqual(true);
    }));

    it('should correctly set selected account user', fakeAsync(() => {
        store.setState(mockedInitialState);

        store.setActiveEntity(mockedAccountUser);

        expect(store.state.activeEntity.scopeState).toEqual(
            ScopeSelectorState.ACCOUNT_SCOPE
        );
        expect(store.state.activeEntity.selectedEntityPermissions).toEqual({
            read: true,
            write: true,
            user: true,
            budget: false,
            agency_spend_margin: false,
            media_cost_data_cost_licence_fee: false,
        });
        expect(store.state.activeEntity.entityAccounts).toEqual([
            mockedAccounts[0],
            mockedAccounts[1],
        ]);
        expect(store.state.activeEntity.selectedAccounts).toEqual([
            mockedAccounts[0],
        ]);
    }));

    it('should correctly set selected agency user', fakeAsync(() => {
        store.setState(mockedInitialState);

        store.setActiveEntity(mockedAgencyUser);

        expect(store.state.activeEntity.scopeState).toEqual(
            ScopeSelectorState.AGENCY_SCOPE
        );
        expect(store.state.activeEntity.selectedEntityPermissions).toEqual({
            read: true,
            write: true,
            user: false,
            budget: false,
            agency_spend_margin: false,
            media_cost_data_cost_licence_fee: false,
        });
        expect(store.state.activeEntity.entityAccounts).toEqual([]);
        expect(store.state.activeEntity.selectedAccounts).toEqual([]);
    }));

    it('should correctly set selected internal user', fakeAsync(() => {
        store.setState(mockedInitialState);

        store.setActiveEntity(mockedInternalUser);

        expect(store.state.activeEntity.scopeState).toEqual(
            ScopeSelectorState.ALL_ACCOUNTS_SCOPE
        );
        expect(store.state.activeEntity.selectedEntityPermissions).toEqual({
            read: true,
            write: false,
            user: false,
            budget: false,
            agency_spend_margin: true,
            media_cost_data_cost_licence_fee: false,
        });
        expect(store.state.activeEntity.entityAccounts).toEqual([]);
        expect(store.state.activeEntity.selectedAccounts).toEqual([]);
    }));

    it('should correctly set selected accounts', fakeAsync(() => {
        store.setState(mockedInitialState);

        store.setActiveEntity(mockedAccountUser);
        store.addActiveEntityAccount(mockedAccounts[2]);

        store.updateSelectedEntityPermissions({
            read: true,
            write: true,
            user: true,
            budget: false,
            agency_spend_margin: false,
            media_cost_data_cost_licence_fee: false,
        });

        store.setSelectedAccounts([mockedAccounts[0]]);

        expect(store.state.activeEntity.selectedAccounts).toEqual([
            mockedAccounts[0],
        ]);
        expect(store.state.activeEntity.selectedEntityPermissions).toEqual({
            read: true,
            write: true,
            user: true,
            budget: false,
            agency_spend_margin: false,
            media_cost_data_cost_licence_fee: false,
        });

        store.setSelectedAccounts([mockedAccounts[1]]);

        expect(store.state.activeEntity.selectedAccounts).toEqual([
            mockedAccounts[1],
        ]);
        expect(store.state.activeEntity.selectedEntityPermissions).toEqual({
            read: true,
            write: true,
            user: false,
            budget: true,
            agency_spend_margin: false,
            media_cost_data_cost_licence_fee: false,
        });

        store.setSelectedAccounts([mockedAccounts[0], mockedAccounts[1]]);

        expect(store.state.activeEntity.selectedAccounts).toEqual([
            mockedAccounts[0],
            mockedAccounts[1],
        ]);
        expect(store.state.activeEntity.selectedEntityPermissions).toEqual({
            read: true,
            write: true,
            user: undefined,
            budget: undefined,
            agency_spend_margin: false,
            media_cost_data_cost_licence_fee: false,
        });

        store.setSelectedAccounts([
            mockedAccounts[0],
            mockedAccounts[1],
            mockedAccounts[2],
        ]);

        expect(store.state.activeEntity.selectedAccounts).toEqual([
            mockedAccounts[0],
            mockedAccounts[1],
            mockedAccounts[2],
        ]);
        expect(store.state.activeEntity.selectedEntityPermissions).toEqual({
            read: true,
            write: true,
            user: undefined,
            budget: undefined,
            agency_spend_margin: false,
            media_cost_data_cost_licence_fee: false,
        });
    }));

    it('should correctly change selected internal permissions', fakeAsync(() => {
        store.setState(mockedInitialState);

        store.setActiveEntity(mockedInternalUser);

        store.updateSelectedEntityPermissions({
            read: true,
            write: true,
            user: true,
            budget: false,
            agency_spend_margin: true,
            media_cost_data_cost_licence_fee: false,
        });

        expect(store.state.activeEntity.selectedEntityPermissions).toEqual({
            read: true,
            write: true,
            user: true,
            budget: false,
            agency_spend_margin: true,
            media_cost_data_cost_licence_fee: false,
        });

        expect(store.state.activeEntity.entity.entityPermissions).toEqual([
            {
                permission: 'read',
            },
            {
                permission: 'write',
            },
            {
                permission: 'user',
            },
            {
                permission: 'agency_spend_margin',
            },
        ]);
    }));

    it('should correctly change selected agency permissions', fakeAsync(() => {
        store.setState(mockedInitialState);

        store.setActiveEntity(mockedAgencyUser);

        store.updateSelectedEntityPermissions({
            read: true,
            write: true,
            user: true,
            budget: false,
            agency_spend_margin: true,
            media_cost_data_cost_licence_fee: false,
        });

        expect(store.state.activeEntity.selectedEntityPermissions).toEqual({
            read: true,
            write: true,
            user: true,
            budget: false,
            agency_spend_margin: true,
            media_cost_data_cost_licence_fee: false,
        });

        expect(store.state.activeEntity.entity.entityPermissions).toEqual([
            {
                agencyId: mockedAgencyId,
                permission: 'read',
            },
            {
                agencyId: mockedAgencyId,
                permission: 'write',
            },
            {
                agencyId: mockedAgencyId,
                permission: 'user',
            },
            {
                agencyId: mockedAgencyId,
                permission: 'agency_spend_margin',
            },
        ]);
    }));

    it('should not allow deselection of all accounts', fakeAsync(() => {
        store.setState(mockedInitialState);

        store.setActiveEntity(mockedAccountUser);
        store.setSelectedAccounts([]);

        expect(store.state.activeEntity.selectedAccounts).toEqual([
            mockedAccounts[0],
        ]);
    }));

    it('should not allow selection of an account that does not belong to the user', fakeAsync(() => {
        store.setState(mockedInitialState);

        store.setActiveEntity(mockedAccountUser);
        store.setSelectedAccounts([mockedAccounts[2]]);

        expect(store.state.activeEntity.selectedAccounts).toEqual([
            mockedAccounts[0],
        ]);
    }));

    it('should correctly change selected account permissions', fakeAsync(() => {
        store.setState(mockedInitialState);

        store.setActiveEntity(mockedAccountUser);
        store.setSelectedAccounts([mockedAccounts[0]]);

        store.updateSelectedEntityPermissions({
            read: true,
            write: true,
            user: true,
            budget: false,
            agency_spend_margin: true,
            media_cost_data_cost_licence_fee: false,
        });

        expect(store.state.activeEntity.selectedEntityPermissions).toEqual({
            read: true,
            write: true,
            user: true,
            budget: false,
            agency_spend_margin: true,
            media_cost_data_cost_licence_fee: false,
        });

        expect(store.state.activeEntity.entity.entityPermissions).toEqual([
            {
                accountId: anotherMockedAccountId,
                permission: 'read',
            },
            {
                accountId: anotherMockedAccountId,
                permission: 'write',
            },
            {
                accountId: anotherMockedAccountId,
                permission: 'budget',
            },
            {
                accountId: mockedAccountId,
                permission: 'read',
            },
            {
                accountId: mockedAccountId,
                permission: 'write',
            },
            {
                accountId: mockedAccountId,
                permission: 'user',
            },
            {
                accountId: mockedAccountId,
                permission: 'agency_spend_margin',
            },
        ]);
    }));

    it('should correctly change account permissions on multiple accounts', fakeAsync(() => {
        store.setState(mockedInitialState);

        store.setActiveEntity(mockedAccountUser);
        store.addActiveEntityAccount(mockedAccounts[2]);
        store.setSelectedAccounts([
            mockedAccounts[0],
            mockedAccounts[1],
            mockedAccounts[2],
        ]);

        // We want read and agency_spend_margin permissions to be added to all accounts
        // We want budget permission to remain unchanged
        // We want all other permissions to be removed from all accounts
        store.updateSelectedEntityPermissions({
            read: true,
            write: false,
            user: false,
            budget: undefined,
            agency_spend_margin: true,
            media_cost_data_cost_licence_fee: false,
        });

        expect(store.state.activeEntity.selectedEntityPermissions).toEqual({
            read: true,
            write: false,
            user: false,
            budget: undefined,
            agency_spend_margin: true,
            media_cost_data_cost_licence_fee: false,
        });

        expect(store.state.activeEntity.entity.entityPermissions).toEqual([
            {
                accountId: anotherMockedAccountId,
                permission: 'budget',
            },
            {
                accountId: mockedAccountId,
                permission: 'read',
            },
            {
                accountId: mockedAccountId,
                permission: 'agency_spend_margin',
            },
            {
                accountId: anotherMockedAccountId,
                permission: 'read',
            },
            {
                accountId: anotherMockedAccountId,
                permission: 'agency_spend_margin',
            },
            {
                accountId: aThirdMockedAccountId,
                permission: 'read',
            },
            {
                accountId: aThirdMockedAccountId,
                permission: 'agency_spend_margin',
            },
        ]);
    }));

    it('should correctly add account to user', fakeAsync(() => {
        store.setState(mockedInitialState);

        store.setActiveEntity(mockedAccountUser);

        expect(store.state.activeEntity.selectedAccounts).toEqual([
            mockedAccounts[0],
        ]);

        store.addActiveEntityAccount(mockedAccounts[2]);

        expect(store.state.activeEntity.entity.entityPermissions).toEqual([
            {
                accountId: mockedAccountId,
                permission: 'read',
            },
            {
                accountId: mockedAccountId,
                permission: 'write',
            },
            {
                accountId: mockedAccountId,
                permission: 'user',
            },
            {
                accountId: anotherMockedAccountId,
                permission: 'read',
            },
            {
                accountId: anotherMockedAccountId,
                permission: 'write',
            },
            {
                accountId: anotherMockedAccountId,
                permission: 'budget',
            },
            {
                accountId: aThirdMockedAccountId,
                permission: 'read',
            },
            {
                accountId: aThirdMockedAccountId,
                permission: 'write',
            },
            {
                accountId: aThirdMockedAccountId,
                permission: 'user',
            },
        ]);

        expect(store.state.activeEntity.entityAccounts).toEqual([
            mockedAccounts[0],
            mockedAccounts[1],
            mockedAccounts[2],
        ]);

        expect(store.state.activeEntity.selectedAccounts).toEqual([
            mockedAccounts[0],
            mockedAccounts[2],
        ]);

        expect(store.state.activeEntity.selectedEntityPermissions).toEqual({
            read: true,
            write: true,
            user: true,
            budget: false,
            agency_spend_margin: false,
            media_cost_data_cost_licence_fee: false,
        });
    }));

    it('should not add account to user if it has already been added', fakeAsync(() => {
        store.setState(mockedInitialState);

        store.setActiveEntity(mockedAccountUser);
        store.addActiveEntityAccount(mockedAccounts[0]);

        expect(store.state.activeEntity.entity.entityPermissions).toEqual([
            {
                accountId: mockedAccountId,
                permission: 'read',
            },
            {
                accountId: mockedAccountId,
                permission: 'write',
            },
            {
                accountId: mockedAccountId,
                permission: 'user',
            },
            {
                accountId: anotherMockedAccountId,
                permission: 'read',
            },
            {
                accountId: anotherMockedAccountId,
                permission: 'write',
            },
            {
                accountId: anotherMockedAccountId,
                permission: 'budget',
            },
        ]);

        expect(store.state.activeEntity.entityAccounts).toEqual([
            mockedAccounts[0],
            mockedAccounts[1],
        ]);
    }));

    it('should correctly remove accounts from a user', fakeAsync(() => {
        store.setState(mockedInitialState);

        store.setActiveEntity(mockedAccountUser);
        store.setSelectedAccounts([mockedAccounts[0], mockedAccounts[1]]);
        store.removeActiveEntityAccounts([mockedAccounts[0]]);

        expect(store.state.activeEntity.entity.entityPermissions).toEqual([
            {
                accountId: anotherMockedAccountId,
                permission: 'read',
            },
            {
                accountId: anotherMockedAccountId,
                permission: 'write',
            },
            {
                accountId: anotherMockedAccountId,
                permission: 'budget',
            },
        ]);

        expect(store.state.activeEntity.selectedAccounts).toEqual([
            mockedAccounts[1],
        ]);

        expect(store.state.activeEntity.entityAccounts).toEqual([
            mockedAccounts[1],
        ]);

        expect(store.state.activeEntity.selectedEntityPermissions).toEqual({
            read: true,
            write: true,
            user: false,
            budget: true,
            agency_spend_margin: false,
            media_cost_data_cost_licence_fee: false,
        });
    }));

    it('should correctly change user scope: account=>agency', fakeAsync(() => {
        store.setState(mockedInitialState);

        store.setActiveEntity(mockedAccountUser);
        store.setActiveEntityScope(ScopeSelectorState.AGENCY_SCOPE);

        expect(store.state.activeEntity.scopeState).toEqual(
            ScopeSelectorState.AGENCY_SCOPE
        );
        expect(store.state.activeEntity.selectedEntityPermissions).toEqual({
            read: true,
            write: false,
            user: false,
            budget: false,
            agency_spend_margin: false,
            media_cost_data_cost_licence_fee: false,
        });
        expect(store.state.activeEntity.entityAccounts).toEqual([]);
        expect(store.state.activeEntity.selectedAccounts).toEqual([]);
    }));

    it('should correctly change user scope: account=>internal', fakeAsync(() => {
        store.setState(mockedInitialState);

        store.setActiveEntity(mockedAccountUser);
        store.setActiveEntityScope(ScopeSelectorState.ALL_ACCOUNTS_SCOPE);

        expect(store.state.activeEntity.scopeState).toEqual(
            ScopeSelectorState.ALL_ACCOUNTS_SCOPE
        );
        expect(store.state.activeEntity.selectedEntityPermissions).toEqual({
            read: true,
            write: false,
            user: false,
            budget: false,
            agency_spend_margin: false,
            media_cost_data_cost_licence_fee: false,
        });
        expect(store.state.activeEntity.entityAccounts).toEqual([]);
        expect(store.state.activeEntity.selectedAccounts).toEqual([]);
    }));

    it('should correctly change user scope: agency=>account', fakeAsync(() => {
        store.setState(mockedInitialState);

        store.setActiveEntity(mockedAgencyUser);
        store.setActiveEntityScope(ScopeSelectorState.ACCOUNT_SCOPE);

        expect(store.state.activeEntity.scopeState).toEqual(
            ScopeSelectorState.ACCOUNT_SCOPE
        );
        expect(store.state.activeEntity.selectedEntityPermissions).toEqual({});
        expect(store.state.activeEntity.entityAccounts).toEqual([]);
        expect(store.state.activeEntity.selectedAccounts).toEqual([]);
    }));

    it('should correctly change user scope: agency=>internal', fakeAsync(() => {
        store.setState(mockedInitialState);

        store.setActiveEntity(mockedAgencyUser);
        store.setActiveEntityScope(ScopeSelectorState.ALL_ACCOUNTS_SCOPE);

        expect(store.state.activeEntity.scopeState).toEqual(
            ScopeSelectorState.ALL_ACCOUNTS_SCOPE
        );
        expect(store.state.activeEntity.selectedEntityPermissions).toEqual({
            read: true,
            write: false,
            user: false,
            budget: false,
            agency_spend_margin: false,
            media_cost_data_cost_licence_fee: false,
        });
        expect(store.state.activeEntity.entityAccounts).toEqual([]);
        expect(store.state.activeEntity.selectedAccounts).toEqual([]);
    }));

    it('should correctly change user scope: internal=>account', fakeAsync(() => {
        store.setState(mockedInitialState);

        store.setActiveEntity(mockedInternalUser);
        store.setActiveEntityScope(ScopeSelectorState.ACCOUNT_SCOPE);

        expect(store.state.activeEntity.scopeState).toEqual(
            ScopeSelectorState.ACCOUNT_SCOPE
        );
        expect(store.state.activeEntity.selectedEntityPermissions).toEqual({});
        expect(store.state.activeEntity.entityAccounts).toEqual([]);
        expect(store.state.activeEntity.selectedAccounts).toEqual([]);
    }));

    it('should correctly change user scope: internal=>agency', fakeAsync(() => {
        store.setState(mockedInitialState);

        store.setActiveEntity(mockedInternalUser);
        store.setActiveEntityScope(ScopeSelectorState.AGENCY_SCOPE);

        expect(store.state.activeEntity.scopeState).toEqual(
            ScopeSelectorState.AGENCY_SCOPE
        );
        expect(store.state.activeEntity.selectedEntityPermissions).toEqual({
            read: true,
            write: false,
            user: false,
            budget: false,
            agency_spend_margin: false,
            media_cost_data_cost_licence_fee: false,
        });
        expect(store.state.activeEntity.entityAccounts).toEqual([]);
        expect(store.state.activeEntity.selectedAccounts).toEqual([]);
    }));

    it('should select all accounts when loading a user who has the same permissions on all accounts', fakeAsync(() => {
        store.setState(mockedInitialState);

        const aNewMockedUser: User = {
            ...mockedAccountUser,
            entityPermissions: [
                {
                    accountId: mockedAccountId,
                    permission: 'read',
                },
                {
                    accountId: mockedAccountId,
                    permission: 'write',
                },
                {
                    accountId: mockedAccountId,
                    permission: 'user',
                },
                {
                    accountId: anotherMockedAccountId,
                    permission: 'read',
                },
                {
                    accountId: anotherMockedAccountId,
                    permission: 'write',
                },
                {
                    accountId: anotherMockedAccountId,
                    permission: 'user',
                },
            ],
        };

        store.setActiveEntity(aNewMockedUser);

        expect(store.state.activeEntity.selectedAccounts).toEqual([
            mockedAccounts[0],
            mockedAccounts[1],
        ]);
    }));
});
