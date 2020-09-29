import {AuthStore} from './auth.store';
import {Injector} from '@angular/core';
import {User} from '../../users/types/user';
import {UserStatus} from '../../../app.constants';
import {SetCurrentUserAction} from './reducers/set-current-user.reducer';
import {FetchCurrentUserActionEffect} from './effects/fetch-current-user.effect';
import {TestBed} from '@angular/core/testing';
import {EntityPermissionValue} from '../../users/users.constants';

describe('AuthStore', () => {
    let fetchCurrentUserActionEffectStub: jasmine.SpyObj<FetchCurrentUserActionEffect>;
    let store: AuthStore;
    let mockedUser: User;

    beforeEach(() => {
        fetchCurrentUserActionEffectStub = jasmine.createSpyObj(
            FetchCurrentUserActionEffect.name,
            ['effect', 'dispatch']
        );
        TestBed.configureTestingModule({
            providers: [
                {
                    provide: FetchCurrentUserActionEffect,
                    useValue: fetchCurrentUserActionEffectStub,
                },
            ],
        });

        store = new AuthStore(TestBed.get(Injector));
        mockedUser = {
            id: '123',
            email: 'test@test.com',
            firstName: 'test',
            lastName: 'test',
            name: 'test tests',
            status: UserStatus.ACTIVE,
            timezoneOffset: -4000,
            intercomUserHash: '$test$',
            defaultCsvSeparator: ',',
            defaultCsvDecimalSeparator: '.',
            permissions: [],
            entityPermissions: [],
        };
    });

    describe('getCurrentUser', () => {
        let user: User;

        beforeEach(() => {
            user = {...mockedUser};
            store.dispatch(new SetCurrentUserAction(user));
        });

        it('should correctly get current user', () => {
            expect(store.getCurrentUser()).toEqual(user);
        });
    });

    describe('hasPermission', () => {
        let user: User;

        beforeEach(() => {
            user = {
                ...mockedUser,
                permissions: [
                    {
                        permission: 'permission.public_1',
                        isPublic: true,
                    },
                    {
                        permission: 'permission.public_2',
                        isPublic: true,
                    },
                    {
                        permission: 'permission.internal_1',
                        isPublic: false,
                    },
                    {
                        permission: 'permission.internal_2',
                        isPublic: false,
                    },
                ],
            };
            store.dispatch(new SetCurrentUserAction(user));
        });

        it('should return false if called without specifying permission', () => {
            expect(store.hasPermission(null)).toBeFalse();
            expect(store.hasPermission(undefined)).toBeFalse();
        });

        it('should return true if user has the specified permission', () => {
            expect(store.hasPermission('permission.public_1')).toBeTrue();
            expect(store.hasPermission('permission.public_2')).toBeTrue();
            expect(store.hasPermission('permission.internal_1')).toBeTrue();
            expect(store.hasPermission('permission.internal_2')).toBeTrue();
        });

        it('should return false if user does not have the specified permission', () => {
            expect(store.hasPermission('permission.unavailable')).toBeFalse();
        });
    });

    describe('isPermissionInternal', () => {
        let user: User;

        beforeEach(() => {
            user = {
                ...mockedUser,
                permissions: [
                    {
                        permission: 'permission.public_1',
                        isPublic: true,
                    },
                    {
                        permission: 'permission.public_2',
                        isPublic: true,
                    },
                    {
                        permission: 'permission.internal_1',
                        isPublic: false,
                    },
                    {
                        permission: 'permission.internal_2',
                        isPublic: false,
                    },
                ],
            };
            store.dispatch(new SetCurrentUserAction(user));
        });

        it('should return false if called without specifying permission', () => {
            expect(store.isPermissionInternal(null)).toBeFalse();
            expect(store.isPermissionInternal(undefined)).toBeFalse();
        });

        it('should return false if specified permission is not internal', () => {
            expect(
                store.isPermissionInternal('permission.public_1')
            ).toBeFalse();
            expect(
                store.isPermissionInternal('permission.public_2')
            ).toBeFalse();
        });

        it('should return true if specified permission is internal', () => {
            expect(
                store.isPermissionInternal('permission.internal_1')
            ).toBeTrue();
            expect(
                store.isPermissionInternal('permission.internal_2')
            ).toBeTrue();
        });
    });

    describe('hasAgencyScope:', () => {
        it("should return false if user doesn't have agency scope for specified agency with entity permissions", () => {
            const user: User = {
                ...mockedUser,
            };
            store.dispatch(new SetCurrentUserAction(user));
            expect(store.hasAgencyScope('9')).toBeFalse();
        });

        it('should return true if user has agency scope for specified agency with entity permissions', () => {
            const user: User = {
                ...mockedUser,
                entityPermissions: [
                    {
                        agencyId: '5',
                        accountId: null,
                        permission: EntityPermissionValue.READ,
                    },
                    {
                        agencyId: '5',
                        accountId: null,
                        permission: EntityPermissionValue.WRITE,
                    },
                ],
            };
            store.dispatch(new SetCurrentUserAction(user));
            expect(store.hasAgencyScope('5')).toBeTrue();
        });
    });

    describe('hasPermissionOn', () => {
        let user: User;

        beforeEach(() => {
            user = {
                ...mockedUser,
                entityPermissions: [
                    {
                        agencyId: null,
                        accountId: '123',
                        permission: EntityPermissionValue.READ,
                    },
                ],
            };
            store.dispatch(new SetCurrentUserAction(user));
        });

        it('should return false if called without specifying entity permission', () => {
            expect(store.hasPermissionOn('123', '123', null)).toBeFalse();
            expect(store.hasPermissionOn('123', '123', undefined)).toBeFalse();
        });

        it('should return true if user has the specified entity permission', () => {
            expect(
                store.hasPermissionOn('123', '123', EntityPermissionValue.READ)
            ).toBeTrue();
        });

        it('should return false if user does not have the specified entity permission', () => {
            expect(
                store.hasPermissionOn('123', '123', EntityPermissionValue.WRITE)
            ).toBeFalse();
        });
    });

    describe('canCreateNewAccount', () => {
        it('should return false if user can not create new account', () => {
            const user: User = {
                ...mockedUser,
            };
            store.dispatch(new SetCurrentUserAction(user));
            expect(store.canCreateNewAccount()).toBeFalse();
        });

        it('should return false if user can not create new account with entity permissions', () => {
            const user: User = {
                ...mockedUser,
            };
            store.dispatch(new SetCurrentUserAction(user));
            expect(store.canCreateNewAccount()).toBeFalse();
        });

        it('should return true if user can create new account with entity permissions', () => {
            const user: User = {
                ...mockedUser,
                entityPermissions: [
                    {
                        agencyId: '5',
                        accountId: null,
                        permission: EntityPermissionValue.READ,
                    },
                    {
                        agencyId: '5',
                        accountId: null,
                        permission: EntityPermissionValue.WRITE,
                    },
                ],
            };
            store.dispatch(new SetCurrentUserAction(user));
            expect(store.canCreateNewAccount()).toBeTrue();
        });
    });

    describe('hasPermissionOnAllEntities', () => {
        it('should return false if called without specifying entity permission', () => {
            expect(store.hasPermissionOnAllEntities(null)).toBeFalse();
            expect(store.hasPermissionOnAllEntities(undefined)).toBeFalse();
        });

        it('should return true if user has the specified entity permission on all entities', () => {
            const user: User = {
                ...mockedUser,
                entityPermissions: [
                    {
                        agencyId: null,
                        accountId: null,
                        permission: EntityPermissionValue.READ,
                    },
                ],
            };
            store.dispatch(new SetCurrentUserAction(user));
            expect(
                store.hasPermissionOnAllEntities(EntityPermissionValue.READ)
            ).toBeTrue();
        });

        it('should return false if user does not have the specified entity permission on all entities', () => {
            const user: User = {
                ...mockedUser,
                entityPermissions: [
                    {
                        agencyId: null,
                        accountId: '123',
                        permission: EntityPermissionValue.READ,
                    },
                ],
            };
            store.dispatch(new SetCurrentUserAction(user));
            expect(
                store.hasPermissionOnAllEntities(EntityPermissionValue.READ)
            ).toBeFalse();
        });
    });

    describe('hasPermissionOnAnyEntities', () => {
        it('should return false if called without specifying entity permission', () => {
            expect(store.hasPermissionOnAnyEntity(null)).toBeFalse();
            expect(store.hasPermissionOnAnyEntity(undefined)).toBeFalse();
        });

        it('should return true if user has the specified entity permission on any entities', () => {
            const user: User = {
                ...mockedUser,
                entityPermissions: [
                    {
                        agencyId: null,
                        accountId: '123',
                        permission: EntityPermissionValue.READ,
                    },
                ],
            };
            store.dispatch(new SetCurrentUserAction(user));
            expect(
                store.hasPermissionOnAnyEntity(EntityPermissionValue.READ)
            ).toBeTrue();
        });

        it('should return false if user does not have the specified entity permission on any entities', () => {
            const user: User = {
                ...mockedUser,
                entityPermissions: [
                    {
                        agencyId: null,
                        accountId: '123',
                        permission: EntityPermissionValue.READ,
                    },
                ],
            };
            store.dispatch(new SetCurrentUserAction(user));
            expect(
                store.hasPermissionOnAnyEntity(EntityPermissionValue.WRITE)
            ).toBeFalse();
        });
    });

    describe('hasReadOnlyAccessOn', () => {
        it('should return true if user has read-only access on account', () => {
            const user: User = {
                ...mockedUser,
                entityPermissions: [
                    {
                        agencyId: null,
                        accountId: '123',
                        permission: EntityPermissionValue.READ,
                    },
                ],
            };
            store.dispatch(new SetCurrentUserAction(user));
            expect(store.hasReadOnlyAccessOn(null, '123')).toBeTrue();
        });

        it('should return true if user has read-only access on agency', () => {
            const user: User = {
                ...mockedUser,
                entityPermissions: [
                    {
                        agencyId: '123',
                        accountId: null,
                        permission: EntityPermissionValue.READ,
                    },
                ],
            };
            store.dispatch(new SetCurrentUserAction(user));
            expect(store.hasReadOnlyAccessOn('123', null)).toBeTrue();
        });

        it('should return false if user has write access on account', () => {
            const user: User = {
                ...mockedUser,
                entityPermissions: [
                    {
                        agencyId: null,
                        accountId: '123',
                        permission: EntityPermissionValue.READ,
                    },
                    {
                        agencyId: null,
                        accountId: '123',
                        permission: EntityPermissionValue.WRITE,
                    },
                ],
            };
            store.dispatch(new SetCurrentUserAction(user));
            expect(store.hasReadOnlyAccessOn(null, '123')).toBeFalse();
        });

        it('should return false if user has write access on agency', () => {
            const user: User = {
                ...mockedUser,
                entityPermissions: [
                    {
                        agencyId: '123',
                        accountId: null,
                        permission: EntityPermissionValue.READ,
                    },
                    {
                        agencyId: '123',
                        accountId: null,
                        permission: EntityPermissionValue.WRITE,
                    },
                ],
            };
            store.dispatch(new SetCurrentUserAction(user));
            expect(store.hasReadOnlyAccessOn('123', null)).toBeFalse();
        });
    });

    describe('hasReadOnlyAccessOnAnyEntity', () => {
        it('should return true if user has read-only access on any entity', () => {
            const user: User = {
                ...mockedUser,
                entityPermissions: [
                    {
                        agencyId: null,
                        accountId: '123',
                        permission: EntityPermissionValue.READ,
                    },
                    {
                        agencyId: null,
                        accountId: '123',
                        permission: EntityPermissionValue.WRITE,
                    },
                    {
                        agencyId: null,
                        accountId: '456',
                        permission: EntityPermissionValue.READ,
                    },
                ],
            };
            store.dispatch(new SetCurrentUserAction(user));
            expect(store.hasReadOnlyAccessOnAnyEntity()).toBeTrue();
        });

        it('should return true if user has write access on all entities', () => {
            const user: User = {
                ...mockedUser,
                entityPermissions: [
                    {
                        agencyId: null,
                        accountId: '123',
                        permission: EntityPermissionValue.READ,
                    },
                    {
                        agencyId: null,
                        accountId: '123',
                        permission: EntityPermissionValue.WRITE,
                    },
                    {
                        agencyId: null,
                        accountId: '456',
                        permission: EntityPermissionValue.READ,
                    },
                    {
                        agencyId: null,
                        accountId: '456',
                        permission: EntityPermissionValue.WRITE,
                    },
                ],
            };
            store.dispatch(new SetCurrentUserAction(user));
            expect(store.hasReadOnlyAccessOnAnyEntity()).toBeFalse();
        });
    });
});
