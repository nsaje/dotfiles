import {AuthStore} from './auth.store';
import {Injector} from '@angular/core';
import {User} from '../../users/types/user';
import {UserStatus} from '../../../app.constants';
import {SetCurrentUserAction} from './reducers/set-current-user.reducer';
import {FetchCurrentUserActionEffect} from './effects/fetch-current-user.effect';
import {TestBed} from '@angular/core/testing';

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
            agencies: [],
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
});
