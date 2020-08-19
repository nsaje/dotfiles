import {
    SetCurrentUserActionReducer,
    SetCurrentUserAction,
} from './set-current-user.reducer';
import {AuthStoreState} from '../auth.store.state';
import {UserStatus} from '../../../../app.constants';
import {User} from '../../../users/types/user';
import {EntityPermissionValue} from '../../../users/users.constants';

describe('SetCurrentUserActionReducer', () => {
    let reducer: SetCurrentUserActionReducer;
    let mockedUser: User;

    beforeEach(() => {
        reducer = new SetCurrentUserActionReducer();
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
            entityPermissions: [
                {
                    agencyId: null,
                    permission: EntityPermissionValue.READ,
                },
                {
                    agencyId: null,
                    permission: EntityPermissionValue.WRITE,
                },
            ],
        };
    });

    it('should correctly reduce state', () => {
        const state = reducer.reduce(
            new AuthStoreState(),
            new SetCurrentUserAction(mockedUser)
        );

        expect(state.user).toEqual(mockedUser);
        expect(state.permissions).toEqual([
            'permission.public_1',
            'permission.public_2',
            'permission.internal_1',
            'permission.internal_2',
        ]);
        expect(state.internalPermissions).toEqual([
            'permission.internal_1',
            'permission.internal_2',
        ]);
    });
});
