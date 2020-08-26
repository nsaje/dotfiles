import * as usersHelpers from './users.helpers';
import {UserStatus} from '../../../app.constants';
import {User} from '../../../core/users/types/user';
import {EntityPermission} from '../../../core/users/types/entity-permission';
import {EntityPermissionValue} from '../../../core/users/users.constants';

describe('UsersHelpers', () => {
    const dummyUser: User = {
        email: '',
        entityPermissions: [],
        status: UserStatus.ACTIVE,
    };

    const accountReadPermission: EntityPermission = {
        accountId: '0',
        permission: EntityPermissionValue.READ,
    };

    const agencyReadPermission: EntityPermission = {
        agencyId: '0',
        permission: EntityPermissionValue.READ,
    };

    const internalReadPermission: EntityPermission = {
        permission: EntityPermissionValue.READ,
    };

    const anotherAccountPermission: EntityPermission = {
        accountId: '0',
        permission: EntityPermissionValue.AGENCY_SPEND_MARGIN,
    };

    const anotherAgencyPermission: EntityPermission = {
        agencyId: '0',
        permission: EntityPermissionValue.AGENCY_SPEND_MARGIN,
    };

    const anotherInternalPermission: EntityPermission = {
        permission: EntityPermissionValue.AGENCY_SPEND_MARGIN,
    };

    it('should determine if a user is an account manager', () => {
        dummyUser.entityPermissions = [accountReadPermission];
        expect(usersHelpers.isAccountManager(dummyUser)).toBeTrue();

        dummyUser.entityPermissions = [anotherAccountPermission];
        expect(usersHelpers.isAccountManager(dummyUser)).toBeFalse();

        dummyUser.entityPermissions = [
            accountReadPermission,
            anotherAccountPermission,
        ];
        expect(usersHelpers.isAccountManager(dummyUser)).toBeTrue();

        dummyUser.entityPermissions = [agencyReadPermission];
        expect(usersHelpers.isAccountManager(dummyUser)).toBeFalse();

        dummyUser.entityPermissions = [
            accountReadPermission,
            agencyReadPermission,
        ];
        expect(usersHelpers.isAccountManager(dummyUser)).toBeTrue();

        dummyUser.entityPermissions = [internalReadPermission];
        expect(usersHelpers.isAccountManager(dummyUser)).toBeFalse();

        dummyUser.entityPermissions = [
            accountReadPermission,
            internalReadPermission,
        ];
        expect(usersHelpers.isAccountManager(dummyUser)).toBeTrue();
    });

    it('should determine if a user is an agency manager', () => {
        dummyUser.entityPermissions = [agencyReadPermission];
        expect(usersHelpers.isAgencyManager(dummyUser)).toBeTrue();

        dummyUser.entityPermissions = [anotherAgencyPermission];
        expect(usersHelpers.isAgencyManager(dummyUser)).toBeFalse();

        dummyUser.entityPermissions = [
            agencyReadPermission,
            anotherAgencyPermission,
        ];
        expect(usersHelpers.isAgencyManager(dummyUser)).toBeTrue();

        dummyUser.entityPermissions = [accountReadPermission];
        expect(usersHelpers.isAgencyManager(dummyUser)).toBeFalse();

        dummyUser.entityPermissions = [
            agencyReadPermission,
            accountReadPermission,
        ];
        expect(usersHelpers.isAgencyManager(dummyUser)).toBeTrue();

        dummyUser.entityPermissions = [internalReadPermission];
        expect(usersHelpers.isAgencyManager(dummyUser)).toBeFalse();

        dummyUser.entityPermissions = [
            agencyReadPermission,
            internalReadPermission,
        ];
        expect(usersHelpers.isAgencyManager(dummyUser)).toBeTrue();
    });

    it('should determine if a user is an internal user', () => {
        dummyUser.entityPermissions = [internalReadPermission];
        expect(usersHelpers.isInternalUser(dummyUser)).toBeTrue();

        dummyUser.entityPermissions = [anotherInternalPermission];
        expect(usersHelpers.isInternalUser(dummyUser)).toBeFalse();

        dummyUser.entityPermissions = [
            internalReadPermission,
            anotherInternalPermission,
        ];
        expect(usersHelpers.isInternalUser(dummyUser)).toBeTrue();

        dummyUser.entityPermissions = [agencyReadPermission];
        expect(usersHelpers.isInternalUser(dummyUser)).toBeFalse();

        dummyUser.entityPermissions = [
            internalReadPermission,
            agencyReadPermission,
        ];
        expect(usersHelpers.isInternalUser(dummyUser)).toBeTrue();

        dummyUser.entityPermissions = [accountReadPermission];
        expect(usersHelpers.isInternalUser(dummyUser)).toBeFalse();

        dummyUser.entityPermissions = [
            internalReadPermission,
            accountReadPermission,
        ];
        expect(usersHelpers.isInternalUser(dummyUser)).toBeTrue();
    });

    it('should return only the permissions that are defined at the highest access level which has READ permission', () => {
        // Only a READ permission => return it
        dummyUser.entityPermissions = [internalReadPermission];
        expect(
            usersHelpers.getHighestLevelEntityPermissions(dummyUser)
        ).toEqual([internalReadPermission]);
        dummyUser.entityPermissions = [agencyReadPermission];
        expect(
            usersHelpers.getHighestLevelEntityPermissions(dummyUser)
        ).toEqual([agencyReadPermission]);
        dummyUser.entityPermissions = [accountReadPermission];
        expect(
            usersHelpers.getHighestLevelEntityPermissions(dummyUser)
        ).toEqual([accountReadPermission]);

        // No READ permissions => return nothing
        dummyUser.entityPermissions = [];
        expect(
            usersHelpers.getHighestLevelEntityPermissions(dummyUser)
        ).toEqual([]);
        dummyUser.entityPermissions = [anotherInternalPermission];
        expect(
            usersHelpers.getHighestLevelEntityPermissions(dummyUser)
        ).toEqual([]);
        dummyUser.entityPermissions = [anotherAgencyPermission];
        expect(
            usersHelpers.getHighestLevelEntityPermissions(dummyUser)
        ).toEqual([]);
        dummyUser.entityPermissions = [anotherAccountPermission];
        expect(
            usersHelpers.getHighestLevelEntityPermissions(dummyUser)
        ).toEqual([]);

        // Two permissions on the same level => return both
        dummyUser.entityPermissions = [
            internalReadPermission,
            anotherInternalPermission,
        ];
        expect(
            usersHelpers.getHighestLevelEntityPermissions(dummyUser)
        ).toEqual([internalReadPermission, anotherInternalPermission]);
        dummyUser.entityPermissions = [
            agencyReadPermission,
            anotherAgencyPermission,
        ];
        expect(
            usersHelpers.getHighestLevelEntityPermissions(dummyUser)
        ).toEqual([agencyReadPermission, anotherAgencyPermission]);
        dummyUser.entityPermissions = [
            accountReadPermission,
            anotherAccountPermission,
        ];
        expect(
            usersHelpers.getHighestLevelEntityPermissions(dummyUser)
        ).toEqual([accountReadPermission, anotherAccountPermission]);

        // Two permissions on different levels => Return only the highest READ permission
        dummyUser.entityPermissions = [
            internalReadPermission,
            anotherAgencyPermission,
        ];
        expect(
            usersHelpers.getHighestLevelEntityPermissions(dummyUser)
        ).toEqual([internalReadPermission]);
        dummyUser.entityPermissions = [
            internalReadPermission,
            anotherAccountPermission,
        ];
        expect(
            usersHelpers.getHighestLevelEntityPermissions(dummyUser)
        ).toEqual([internalReadPermission]);
        dummyUser.entityPermissions = [
            agencyReadPermission,
            anotherInternalPermission,
        ];
        expect(
            usersHelpers.getHighestLevelEntityPermissions(dummyUser)
        ).toEqual([agencyReadPermission]);
        dummyUser.entityPermissions = [
            agencyReadPermission,
            anotherAccountPermission,
        ];
        expect(
            usersHelpers.getHighestLevelEntityPermissions(dummyUser)
        ).toEqual([agencyReadPermission]);
        dummyUser.entityPermissions = [
            accountReadPermission,
            anotherInternalPermission,
        ];
        expect(
            usersHelpers.getHighestLevelEntityPermissions(dummyUser)
        ).toEqual([accountReadPermission]);
        dummyUser.entityPermissions = [
            accountReadPermission,
            anotherAgencyPermission,
        ];
        expect(
            usersHelpers.getHighestLevelEntityPermissions(dummyUser)
        ).toEqual([accountReadPermission]);
    });
});
