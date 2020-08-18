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
import {EntityPermissionValue} from '../../../../core/users/types/entity-permission-value';
import {AuthStore} from '../../../../core/auth/services/auth.store';
import {UserStatus} from '../../../../app.constants';

function mockUserCantSeeServiceFeeOnAccount(
    authStoreStub: jasmine.SpyObj<AuthStore>,
    mockedAccountId: string
) {
    authStoreStub.hasEntityPermission.and
        .callFake(
            (
                agencyId: string,
                accountId: string,
                permission: EntityPermissionValue
            ) => {
                if (
                    accountId === mockedAccountId &&
                    permission === 'base_costs_service_fee'
                ) {
                    return false;
                } else {
                    return true;
                }
            }
        )
        .calls.reset();
}

function mockUserCantSeeServiceFeeOnAgency(
    authStoreStub: jasmine.SpyObj<AuthStore>,
    mockedAgencyId: string
) {
    authStoreStub.hasEntityPermission.and
        .callFake(
            (
                agencyId: string,
                accountId: string,
                permission: EntityPermissionValue
            ) => {
                if (
                    agencyId === mockedAgencyId &&
                    permission === 'base_costs_service_fee'
                ) {
                    return false;
                } else {
                    return true;
                }
            }
        )
        .calls.reset();
}

function mockUserCantSeeServiceFeeInternal(
    authStoreStub: jasmine.SpyObj<AuthStore>
) {
    authStoreStub.hasEntityPermission.and
        .callFake(
            (
                agencyId: string,
                accountId: string,
                permission: EntityPermissionValue
            ) => {
                if (permission === 'base_costs_service_fee') {
                    return false;
                } else {
                    return true;
                }
            }
        )
        .calls.reset();
}

describe('UsersStore', () => {
    let usersServiceStub: jasmine.SpyObj<UsersService>;
    let accountsServiceStub: jasmine.SpyObj<AccountService>;
    let authStoreStub: jasmine.SpyObj<AuthStore>;
    let store: UsersStore;
    let mockedAccountUser: User;
    let mockedAgencyUser: User;
    let mockedInternalUser: User;
    let mockedUsers: User[];
    let mockedAgencyId: string;
    let mockedAccount0Id: string;
    let mockedAccount1Id: string;
    let mockedAccount2Id: string;
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
        authStoreStub = jasmine.createSpyObj(AuthStore.name, [
            'hasEntityPermission',
            'hasEntityPermission',
            'getCurrentUserId',
        ]);

        store = new UsersStore(
            usersServiceStub,
            accountsServiceStub,
            authStoreStub
        );

        mockedAgencyId = '10';
        mockedAccount0Id = '515';
        mockedAccount1Id = '525';
        mockedAccount2Id = '535';

        mockedAccountUser = {
            id: '10000001',
            email: 'account.user@outbrain.com',
            firstName: 'Account',
            lastName: 'User',
            entityPermissions: [
                {
                    accountId: mockedAccount0Id,
                    permission: 'read',
                },
                {
                    accountId: mockedAccount0Id,
                    permission: 'write',
                },
                {
                    accountId: mockedAccount0Id,
                    permission: 'user',
                },
                {
                    accountId: mockedAccount1Id,
                    permission: 'read',
                },
                {
                    accountId: mockedAccount1Id,
                    permission: 'write',
                },
                {
                    accountId: mockedAccount1Id,
                    permission: 'budget',
                },
            ],
            status: UserStatus.ACTIVE,
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
            status: UserStatus.ACTIVE,
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
            status: UserStatus.ACTIVE,
        };
        mockedUsers = [mockedAccountUser, mockedAgencyUser, mockedInternalUser];

        mockedAccounts = [
            {
                ...mockHelpers.getMockedAccount(),
                id: mockedAccount0Id,
            },
            {
                ...mockHelpers.getMockedAccount(),
                id: mockedAccount1Id,
            },
            {
                ...mockHelpers.getMockedAccount(),
                id: mockedAccount2Id,
            },
        ];

        mockedInitialState = {
            ...new UsersStoreState(),
            agencyId: mockedAgencyId,
            accountId: mockedAccount0Id,
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
        authStoreStub.getCurrentUserId.and.returnValue('42').calls.reset();
        authStoreStub.hasEntityPermission.and.returnValue(true).calls.reset();
    });

    it('should correctly initialize store', fakeAsync(() => {
        store.setStore(mockedAgencyId, mockedAccount0Id, 1, 10, '', true);
        tick();

        expect(store.state.agencyId).toEqual(mockedAgencyId);
        expect(store.state.accountId).toEqual(mockedAccount0Id);
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
            mockedAccount0Id,
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
            mockedAccount0Id,
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
            status: UserStatus.ACTIVE,
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
                status: UserStatus.ACTIVE,
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
                status: UserStatus.ACTIVE,
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
                status: UserStatus.ACTIVE,
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
                status: UserStatus.ACTIVE,
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
            mockedAccount0Id,
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
            mockedAccount0Id,
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
            base_costs_service_fee: false,
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
            base_costs_service_fee: false,
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
            base_costs_service_fee: false,
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
            base_costs_service_fee: false,
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
            base_costs_service_fee: false,
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
            base_costs_service_fee: false,
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
            base_costs_service_fee: false,
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
            base_costs_service_fee: false,
        });

        expect(store.state.activeEntity.selectedEntityPermissions).toEqual({
            read: true,
            write: true,
            user: true,
            budget: false,
            agency_spend_margin: true,
            media_cost_data_cost_licence_fee: false,
            base_costs_service_fee: false,
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
            base_costs_service_fee: false,
        });

        expect(store.state.activeEntity.selectedEntityPermissions).toEqual({
            read: true,
            write: true,
            user: true,
            budget: false,
            agency_spend_margin: true,
            media_cost_data_cost_licence_fee: false,
            base_costs_service_fee: false,
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
            base_costs_service_fee: false,
        });

        expect(store.state.activeEntity.selectedEntityPermissions).toEqual({
            read: true,
            write: true,
            user: true,
            budget: false,
            agency_spend_margin: true,
            media_cost_data_cost_licence_fee: false,
            base_costs_service_fee: false,
        });

        expect(store.state.activeEntity.entity.entityPermissions).toEqual([
            {
                accountId: mockedAccount1Id,
                permission: 'read',
            },
            {
                accountId: mockedAccount1Id,
                permission: 'write',
            },
            {
                accountId: mockedAccount1Id,
                permission: 'budget',
            },
            {
                accountId: mockedAccount0Id,
                permission: 'read',
            },
            {
                accountId: mockedAccount0Id,
                permission: 'write',
            },
            {
                accountId: mockedAccount0Id,
                permission: 'user',
            },
            {
                accountId: mockedAccount0Id,
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
            base_costs_service_fee: false,
        });

        expect(store.state.activeEntity.selectedEntityPermissions).toEqual({
            read: true,
            write: false,
            user: false,
            budget: undefined,
            agency_spend_margin: true,
            media_cost_data_cost_licence_fee: false,
            base_costs_service_fee: false,
        });

        expect(store.state.activeEntity.entity.entityPermissions).toEqual([
            {
                accountId: mockedAccount1Id,
                permission: 'budget',
            },
            {
                accountId: mockedAccount0Id,
                permission: 'read',
            },
            {
                accountId: mockedAccount0Id,
                permission: 'agency_spend_margin',
            },
            {
                accountId: mockedAccount1Id,
                permission: 'read',
            },
            {
                accountId: mockedAccount1Id,
                permission: 'agency_spend_margin',
            },
            {
                accountId: mockedAccount2Id,
                permission: 'read',
            },
            {
                accountId: mockedAccount2Id,
                permission: 'agency_spend_margin',
            },
        ]);
    }));

    it('should not remove the readonly attribute when permissions are changed on account', fakeAsync(() => {
        mockUserCantSeeServiceFeeOnAccount(authStoreStub, mockedAccount0Id);
        store.setState(mockedInitialState);

        const aNewMockedUser: User = {
            ...mockedAccountUser,
            entityPermissions: [
                {
                    accountId: mockedAccount0Id,
                    permission: 'read',
                },
                {
                    accountId: mockedAccount0Id,
                    permission: 'agency_spend_margin',
                    readonly: true,
                },
                {
                    accountId: mockedAccount0Id,
                    permission: 'media_cost_data_cost_licence_fee',
                    readonly: true,
                },
            ],
        };

        store.setActiveEntity(aNewMockedUser);

        store.updateSelectedEntityPermissions({
            read: true,
            write: true,
            user: true,
            budget: false,
            agency_spend_margin: true,
            media_cost_data_cost_licence_fee: true,
            base_costs_service_fee: false,
        });

        expect(store.state.activeEntity.selectedEntityPermissions).toEqual({
            read: true,
            write: true,
            user: true,
            budget: false,
            agency_spend_margin: true,
            media_cost_data_cost_licence_fee: true,
            base_costs_service_fee: false,
        });

        expect(store.state.activeEntity.entity.entityPermissions).toEqual([
            {
                accountId: mockedAccount0Id,
                permission: 'read',
            },
            {
                accountId: mockedAccount0Id,
                permission: 'write',
            },
            {
                accountId: mockedAccount0Id,
                permission: 'user',
            },
            {
                accountId: mockedAccount0Id,
                permission: 'agency_spend_margin',
                readonly: true,
            },
            {
                accountId: mockedAccount0Id,
                permission: 'media_cost_data_cost_licence_fee',
                readonly: true,
            },
        ]);
    }));

    it('should not remove the readonly attribute when permissions are changed on agency', fakeAsync(() => {
        mockUserCantSeeServiceFeeOnAgency(authStoreStub, mockedAgencyId);
        store.setState(mockedInitialState);

        const aNewMockedUser: User = {
            ...mockedAgencyUser,
            entityPermissions: [
                {
                    agencyId: mockedAgencyId,
                    permission: 'read',
                },
                {
                    agencyId: mockedAgencyId,
                    permission: 'agency_spend_margin',
                    readonly: true,
                },
                {
                    agencyId: mockedAgencyId,
                    permission: 'media_cost_data_cost_licence_fee',
                    readonly: true,
                },
            ],
        };

        store.setActiveEntity(aNewMockedUser);

        store.updateSelectedEntityPermissions({
            read: true,
            write: true,
            user: true,
            budget: false,
            agency_spend_margin: true,
            media_cost_data_cost_licence_fee: true,
            base_costs_service_fee: false,
        });

        expect(store.state.activeEntity.selectedEntityPermissions).toEqual({
            read: true,
            write: true,
            user: true,
            budget: false,
            agency_spend_margin: true,
            media_cost_data_cost_licence_fee: true,
            base_costs_service_fee: false, // This is false, because the user can't see this permission
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
                readonly: true,
            },
            {
                agencyId: mockedAgencyId,
                permission: 'media_cost_data_cost_licence_fee',
                readonly: true,
            },
        ]);
    }));

    it('should not remove the readonly attribute when permissions are changed - internal', fakeAsync(() => {
        mockUserCantSeeServiceFeeInternal(authStoreStub);
        store.setState(mockedInitialState);

        const aNewMockedUser: User = {
            ...mockedInternalUser,
            entityPermissions: [
                {
                    agencyId: mockedAgencyId,
                    permission: 'read',
                },
                {
                    agencyId: mockedAgencyId,
                    permission: 'agency_spend_margin',
                    readonly: true,
                },
                {
                    agencyId: mockedAgencyId,
                    permission: 'media_cost_data_cost_licence_fee',
                    readonly: true,
                },
            ],
        };

        store.setActiveEntity(aNewMockedUser);

        store.updateSelectedEntityPermissions({
            read: true,
            write: true,
            user: true,
            budget: false,
            agency_spend_margin: true,
            media_cost_data_cost_licence_fee: true,
            base_costs_service_fee: false,
        });

        expect(store.state.activeEntity.selectedEntityPermissions).toEqual({
            read: true,
            write: true,
            user: true,
            budget: false,
            agency_spend_margin: true,
            media_cost_data_cost_licence_fee: true,
            base_costs_service_fee: false, // This is false, because the user can't see this permission
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
                readonly: true,
            },
            {
                agencyId: mockedAgencyId,
                permission: 'media_cost_data_cost_licence_fee',
                readonly: true,
            },
        ]);
    }));

    it('should not allow changing of readonly permissions', fakeAsync(() => {
        mockUserCantSeeServiceFeeInternal(authStoreStub);
        store.setState(mockedInitialState);

        const aNewMockedUser: User = {
            ...mockedAgencyUser,
            entityPermissions: [
                {
                    agencyId: mockedAgencyId,
                    permission: 'read',
                },
                {
                    agencyId: mockedAgencyId,
                    permission: 'agency_spend_margin',
                    readonly: true,
                },
                {
                    agencyId: mockedAgencyId,
                    permission: 'media_cost_data_cost_licence_fee',
                    readonly: true,
                },
            ],
        };

        store.setActiveEntity(aNewMockedUser);

        expect(() => {
            store.updateSelectedEntityPermissions({
                read: true,
                write: true,
                user: true,
                budget: false,
                agency_spend_margin: true,
                media_cost_data_cost_licence_fee: false,
                base_costs_service_fee: false,
            });
        }).toThrow(new Error('Disabled or hidden checkbox cannot be changed!'));
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
                accountId: mockedAccount0Id,
                permission: 'read',
            },
            {
                accountId: mockedAccount0Id,
                permission: 'write',
            },
            {
                accountId: mockedAccount0Id,
                permission: 'user',
            },
            {
                accountId: mockedAccount1Id,
                permission: 'read',
            },
            {
                accountId: mockedAccount1Id,
                permission: 'write',
            },
            {
                accountId: mockedAccount1Id,
                permission: 'budget',
            },
            {
                accountId: mockedAccount2Id,
                permission: 'read',
            },
            {
                accountId: mockedAccount2Id,
                permission: 'write',
            },
            {
                accountId: mockedAccount2Id,
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
            base_costs_service_fee: false,
        });
    }));

    it('should not add account to user if it has already been added', fakeAsync(() => {
        store.setState(mockedInitialState);

        store.setActiveEntity(mockedAccountUser);
        store.addActiveEntityAccount(mockedAccounts[0]);

        expect(store.state.activeEntity.entity.entityPermissions).toEqual([
            {
                accountId: mockedAccount0Id,
                permission: 'read',
            },
            {
                accountId: mockedAccount0Id,
                permission: 'write',
            },
            {
                accountId: mockedAccount0Id,
                permission: 'user',
            },
            {
                accountId: mockedAccount1Id,
                permission: 'read',
            },
            {
                accountId: mockedAccount1Id,
                permission: 'write',
            },
            {
                accountId: mockedAccount1Id,
                permission: 'budget',
            },
        ]);

        expect(store.state.activeEntity.entityAccounts).toEqual([
            mockedAccounts[0],
            mockedAccounts[1],
        ]);
    }));

    it("should not copy a permission to a new account if the app user hasn't got the permission to use it", fakeAsync(() => {
        authStoreStub.hasEntityPermission.and
            .callFake(
                (
                    agencyId: string,
                    accountId: string,
                    permission: EntityPermissionValue
                ) => {
                    if (
                        accountId === mockedAccount1Id &&
                        permission === 'budget'
                    ) {
                        return false;
                    } else {
                        return true;
                    }
                }
            )
            .calls.reset();

        store.setState(mockedInitialState);

        const aNewMockedUser: User = {
            ...mockedAccountUser,
            entityPermissions: [
                {
                    accountId: mockedAccount0Id,
                    permission: 'read',
                },
                {
                    accountId: mockedAccount0Id,
                    permission: 'write',
                },
                {
                    accountId: mockedAccount0Id,
                    permission: 'budget',
                },
            ],
        };

        store.setActiveEntity(aNewMockedUser);
        store.addActiveEntityAccount(mockedAccounts[1]);

        expect(store.state.activeEntity.entity.entityPermissions).toEqual([
            {
                accountId: mockedAccount0Id,
                permission: 'read',
            },
            {
                accountId: mockedAccount0Id,
                permission: 'write',
            },
            {
                accountId: mockedAccount0Id,
                permission: 'budget',
            },
            {
                accountId: mockedAccount1Id,
                permission: 'read',
            },
            {
                accountId: mockedAccount1Id,
                permission: 'write',
            },
        ]);
    }));

    it('should correctly remove accounts from a user', fakeAsync(() => {
        store.setState(mockedInitialState);

        store.setActiveEntity(mockedAccountUser);
        store.setSelectedAccounts([mockedAccounts[0], mockedAccounts[1]]);
        store.removeActiveEntityAccounts([mockedAccounts[0]]);

        expect(store.state.activeEntity.entity.entityPermissions).toEqual([
            {
                accountId: mockedAccount1Id,
                permission: 'read',
            },
            {
                accountId: mockedAccount1Id,
                permission: 'write',
            },
            {
                accountId: mockedAccount1Id,
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
            base_costs_service_fee: false,
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
            base_costs_service_fee: false,
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
            base_costs_service_fee: false,
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
            base_costs_service_fee: false,
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
            base_costs_service_fee: false,
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
                    accountId: mockedAccount0Id,
                    permission: 'read',
                },
                {
                    accountId: mockedAccount0Id,
                    permission: 'write',
                },
                {
                    accountId: mockedAccount0Id,
                    permission: 'user',
                },
                {
                    accountId: mockedAccount1Id,
                    permission: 'read',
                },
                {
                    accountId: mockedAccount1Id,
                    permission: 'write',
                },
                {
                    accountId: mockedAccount1Id,
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

    it('should show and enable all checkboxes except total_spend if the calling user has permission to change all of them', fakeAsync(() => {
        store.setState(mockedInitialState);

        const aNewMockedUser: User = {
            ...mockedAccountUser,
            entityPermissions: [
                {
                    accountId: mockedAccount0Id,
                    permission: 'read',
                },
            ],
        };

        store.setActiveEntity(aNewMockedUser);

        expect(store.state.activeEntity.checkboxStates).toEqual({
            write: 'enabled',
            user: 'enabled',
            budget: 'enabled',
            total_spend: 'disabled',
            agency_spend_margin: 'enabled',
            media_cost_data_cost_licence_fee: 'enabled',
            base_costs_service_fee: 'enabled',
        });
    }));

    it("should disable a general permission checkbox if the user hasn't got the permission to use it", fakeAsync(() => {
        authStoreStub.hasEntityPermission.and
            .callFake(
                (
                    agencyId: string,
                    accountId: string,
                    permission: EntityPermissionValue
                ) => {
                    if (
                        accountId === mockedAccount0Id &&
                        permission === 'budget'
                    ) {
                        return false;
                    } else {
                        return true;
                    }
                }
            )
            .calls.reset();

        store.setState(mockedInitialState);

        const aNewMockedUser: User = {
            ...mockedAccountUser,
            entityPermissions: [
                {
                    accountId: mockedAccount0Id,
                    permission: 'read',
                },
                {
                    accountId: mockedAccount1Id,
                    permission: 'read',
                },
            ],
        };

        store.setActiveEntity(aNewMockedUser);
        store.setSelectedAccounts([mockedAccounts[0]]);

        expect(store.state.activeEntity.checkboxStates).toEqual({
            write: 'enabled',
            user: 'enabled',
            budget: 'disabled',
            total_spend: 'disabled',
            agency_spend_margin: 'enabled',
            media_cost_data_cost_licence_fee: 'enabled',
            base_costs_service_fee: 'enabled',
        });

        store.setSelectedAccounts([mockedAccounts[1]]);

        expect(store.state.activeEntity.checkboxStates).toEqual({
            write: 'enabled',
            user: 'enabled',
            budget: 'enabled',
            total_spend: 'disabled',
            agency_spend_margin: 'enabled',
            media_cost_data_cost_licence_fee: 'enabled',
            base_costs_service_fee: 'enabled',
        });

        store.setSelectedAccounts([mockedAccounts[0], mockedAccounts[1]]);

        expect(store.state.activeEntity.checkboxStates).toEqual({
            write: 'enabled',
            user: 'enabled',
            budget: 'disabled',
            total_spend: 'disabled',
            agency_spend_margin: 'enabled',
            media_cost_data_cost_licence_fee: 'enabled',
            base_costs_service_fee: 'enabled',
        });
    }));

    it("should hide a reporting permission checkbox if the user hasn't got the permission to use it", fakeAsync(() => {
        mockUserCantSeeServiceFeeOnAccount(authStoreStub, mockedAccount0Id);

        store.setState(mockedInitialState);

        const aNewMockedUser: User = {
            ...mockedAccountUser,
            entityPermissions: [
                {
                    accountId: mockedAccount0Id,
                    permission: 'read',
                },
                {
                    accountId: mockedAccount1Id,
                    permission: 'read',
                },
            ],
        };

        store.setActiveEntity(aNewMockedUser);
        store.setSelectedAccounts([mockedAccounts[0]]);

        expect(store.state.activeEntity.checkboxStates).toEqual({
            write: 'enabled',
            user: 'enabled',
            budget: 'enabled',
            total_spend: 'disabled',
            agency_spend_margin: 'enabled',
            media_cost_data_cost_licence_fee: 'enabled',
            base_costs_service_fee: 'hidden',
        });

        store.setSelectedAccounts([mockedAccounts[1]]);

        expect(store.state.activeEntity.checkboxStates).toEqual({
            write: 'enabled',
            user: 'enabled',
            budget: 'enabled',
            total_spend: 'disabled',
            agency_spend_margin: 'enabled',
            media_cost_data_cost_licence_fee: 'enabled',
            base_costs_service_fee: 'enabled',
        });
    }));

    it("should disable all reporting checkboxes and set a reporting permission's checkbox to indeterminate if the user has its permission only on some selected accounts", fakeAsync(() => {
        mockUserCantSeeServiceFeeOnAccount(authStoreStub, mockedAccount0Id);

        store.setState(mockedInitialState);

        const aNewMockedUser: User = {
            ...mockedAccountUser,
            entityPermissions: [
                {
                    accountId: mockedAccount0Id,
                    permission: 'read',
                },
                {
                    accountId: mockedAccount1Id,
                    permission: 'read',
                },
            ],
        };

        store.setActiveEntity(aNewMockedUser);
        store.setSelectedAccounts([mockedAccounts[0], mockedAccounts[1]]);

        expect(store.state.activeEntity.checkboxStates).toEqual({
            write: 'enabled',
            user: 'enabled',
            budget: 'enabled',
            total_spend: 'disabled',
            agency_spend_margin: 'disabled',
            media_cost_data_cost_licence_fee: 'disabled',
            base_costs_service_fee: 'disabled',
        });

        expect(store.state.activeEntity.selectedEntityPermissions).toEqual({
            read: true,
            write: false,
            user: false,
            budget: false,
            agency_spend_margin: false,
            media_cost_data_cost_licence_fee: false,
            base_costs_service_fee: undefined,
        });
    }));

    it('should disable all reporting checkboxes if some in the current selection are readonly - account', fakeAsync(() => {
        mockUserCantSeeServiceFeeOnAccount(authStoreStub, mockedAccount0Id);

        store.setState(mockedInitialState);

        const aNewMockedUser: User = {
            ...mockedAccountUser,
            entityPermissions: [
                {
                    accountId: mockedAccount0Id,
                    permission: 'read',
                },
                {
                    accountId: mockedAccount0Id,
                    permission: 'agency_spend_margin',
                    readonly: true,
                },
                {
                    accountId: mockedAccount0Id,
                    permission: 'media_cost_data_cost_licence_fee',
                    readonly: true,
                },
                {
                    accountId: mockedAccount1Id,
                    permission: 'read',
                },
                {
                    accountId: mockedAccount1Id,
                    permission: 'agency_spend_margin',
                },
                {
                    accountId: mockedAccount1Id,
                    permission: 'media_cost_data_cost_licence_fee',
                },
                {
                    accountId: mockedAccount1Id,
                    permission: 'base_costs_service_fee',
                },
            ],
        };

        store.setActiveEntity(aNewMockedUser);
        store.setSelectedAccounts([mockedAccounts[1]]);

        expect(store.state.activeEntity.checkboxStates).toEqual({
            write: 'enabled',
            user: 'enabled',
            budget: 'enabled',
            total_spend: 'disabled',
            agency_spend_margin: 'enabled',
            media_cost_data_cost_licence_fee: 'enabled',
            base_costs_service_fee: 'enabled',
        });

        store.setSelectedAccounts([mockedAccounts[0]]);

        expect(store.state.activeEntity.checkboxStates).toEqual({
            write: 'enabled',
            user: 'enabled',
            budget: 'enabled',
            total_spend: 'disabled',
            agency_spend_margin: 'disabled',
            media_cost_data_cost_licence_fee: 'disabled',
            base_costs_service_fee: 'hidden',
        });

        store.setSelectedAccounts([mockedAccounts[0], mockedAccounts[1]]);

        expect(store.state.activeEntity.checkboxStates).toEqual({
            write: 'enabled',
            user: 'enabled',
            budget: 'enabled',
            total_spend: 'disabled',
            agency_spend_margin: 'disabled',
            media_cost_data_cost_licence_fee: 'disabled',
            base_costs_service_fee: 'disabled',
        });
    }));

    it('should disable all reporting checkboxes if some in the current selection are readonly - agency', fakeAsync(() => {
        mockUserCantSeeServiceFeeOnAgency(authStoreStub, mockedAgencyId);

        store.setState(mockedInitialState);

        const aNewMockedUser: User = {
            ...mockedAgencyUser,
            entityPermissions: [
                {
                    agencyId: mockedAgencyId,
                    permission: 'read',
                },
                {
                    agencyId: mockedAgencyId,
                    permission: 'agency_spend_margin',
                    readonly: true,
                },
                {
                    agencyId: mockedAgencyId,
                    permission: 'media_cost_data_cost_licence_fee',
                    readonly: true,
                },
            ],
        };

        store.setActiveEntity(aNewMockedUser);

        expect(store.state.activeEntity.checkboxStates).toEqual({
            write: 'enabled',
            user: 'enabled',
            budget: 'enabled',
            total_spend: 'disabled',
            agency_spend_margin: 'disabled',
            media_cost_data_cost_licence_fee: 'disabled',
            base_costs_service_fee: 'hidden',
        });
    }));

    it('should disable all reporting checkboxes if some in the current selection are readonly - internal', fakeAsync(() => {
        mockUserCantSeeServiceFeeInternal(authStoreStub);

        store.setState(mockedInitialState);

        const aNewMockedUser: User = {
            ...mockedInternalUser,
            entityPermissions: [
                {
                    permission: 'read',
                },
                {
                    permission: 'agency_spend_margin',
                    readonly: true,
                },
                {
                    permission: 'media_cost_data_cost_licence_fee',
                    readonly: true,
                },
            ],
        };

        store.setActiveEntity(aNewMockedUser);

        expect(store.state.activeEntity.checkboxStates).toEqual({
            write: 'enabled',
            user: 'enabled',
            budget: 'enabled',
            total_spend: 'disabled',
            agency_spend_margin: 'disabled',
            media_cost_data_cost_licence_fee: 'disabled',
            base_costs_service_fee: 'hidden',
        });
    }));
});
