import * as usersGridHelpers from './users-grid.helpers';
import {User} from '../../../../../core/users/types/user';
import {EntityPermissionValue} from '../../../../../core/users/types/entity-permission-value';
import {UserStatus} from '../../../../../app.constants';

describe('ArrayHelpers', () => {
    const dummyUser: User = {
        email: '',
        entityPermissions: [],
        status: UserStatus.ACTIVE,
    };
    const interestingPermissions: EntityPermissionValue[] = [
        'user',
        'agency_spend_margin',
    ];
    const interestingAccountId = '0';

    it('should return a list of those selected permissions that we are interested on the account we are interested in', () => {
        dummyUser.entityPermissions = [
            {
                accountId: interestingAccountId,
                permission: 'read',
            },
            {
                accountId: interestingAccountId,
                permission: 'user',
            },
            {
                accountId: interestingAccountId,
                permission: 'agency_spend_margin',
            },
        ];
        expect(
            usersGridHelpers.getPermissionsText(
                dummyUser,
                interestingAccountId,
                interestingPermissions
            )
        ).toEqual('Manage users, Campaign margin');

        dummyUser.entityPermissions = [
            {
                accountId: interestingAccountId,
                permission: 'read',
            },
            {
                accountId: interestingAccountId,
                permission: 'user',
            },
            {
                accountId: '123',
                permission: 'agency_spend_margin',
            },
        ];
        expect(
            usersGridHelpers.getPermissionsText(
                dummyUser,
                interestingAccountId,
                interestingPermissions
            )
        ).toEqual('Manage users');
    });

    it('should return "N/A" when we try to get the list of permissions of an account manager without specifying accountId', () => {
        dummyUser.entityPermissions = [
            {
                accountId: interestingAccountId,
                permission: 'read',
            },
            {
                accountId: interestingAccountId,
                permission: 'user',
            },
            {
                accountId: '123',
                permission: 'agency_spend_margin',
            },
        ];
        expect(
            usersGridHelpers.getPermissionsText(
                dummyUser,
                null,
                interestingPermissions
            )
        ).toEqual('N/A');
    });

    it('should return an empty string if user has no permissions on the specified account', () => {
        dummyUser.entityPermissions = [
            {
                accountId: '123',
                permission: 'read',
            },
            {
                accountId: '123',
                permission: 'user',
            },
            {
                accountId: '123',
                permission: 'agency_spend_margin',
            },
        ];
        expect(
            usersGridHelpers.getPermissionsText(
                dummyUser,
                interestingAccountId,
                interestingPermissions
            )
        ).toEqual('');
    });

    it('should return a list of agency-level permissions of agency manager if we specify accountId', () => {
        dummyUser.entityPermissions = [
            {
                agencyId: '123',
                permission: 'read',
            },
            {
                agencyId: '123',
                permission: 'agency_spend_margin',
            },
        ];
        expect(
            usersGridHelpers.getPermissionsText(
                dummyUser,
                interestingAccountId,
                interestingPermissions
            )
        ).toEqual('Campaign margin');
    });

    it('should return a list of agency-level permissions of agency manager if we do not specify accountId', () => {
        dummyUser.entityPermissions = [
            {
                agencyId: '123',
                permission: 'read',
            },
            {
                agencyId: '123',
                permission: 'user',
            },
            {
                agencyId: '123',
                permission: 'agency_spend_margin',
            },
        ];
        expect(
            usersGridHelpers.getPermissionsText(
                dummyUser,
                null,
                interestingPermissions
            )
        ).toEqual('Manage users, Campaign margin');
    });

    it('should return an empty string if agency-level user has no permissions that we are interested in', () => {
        dummyUser.entityPermissions = [
            {
                agencyId: '123',
                permission: 'read',
            },
            {
                agencyId: '123',
                permission: 'write',
            },
        ];
        expect(
            usersGridHelpers.getPermissionsText(
                dummyUser,
                interestingAccountId,
                interestingPermissions
            )
        ).toEqual('');
    });

    it('should eliminate duplicate values from the list', () => {
        dummyUser.entityPermissions = [
            {
                agencyId: '012',
                permission: 'user',
            },
            {
                agencyId: '123',
                permission: 'user',
            },
        ];
        expect(
            usersGridHelpers.getPermissionsText(
                dummyUser,
                null,
                interestingPermissions
            )
        ).toEqual('Manage users');
    });
});
