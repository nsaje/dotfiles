import {User} from '../../../../../core/users/types/user';
import {DisplayedEntityPermissionValue} from '../../../types/displayed-entity-permission-value';
import {EntityPermission} from '../../../../../core/users/types/entity-permission';
import {isDefined} from '../../../../../shared/helpers/common.helpers';
import {distinct} from '../../../../../shared/helpers/array.helpers';
import {ENTITY_PERMISSION_VALUE_TO_SHORT_NAME} from '../../../users.config';
import {
    getHighestLevelEntityPermissions,
    isAccountManager,
    isAgencyManager,
    isInternalUser,
} from '../../../helpers/users.helpers';

export function getPermissionsText(
    user: User,
    accountId: string,
    permissionsInColumn: DisplayedEntityPermissionValue[]
): string {
    const filteredPermissions: EntityPermission[] = permissionsInColumn
        .map(permission =>
            getHighestLevelEntityPermissions(user).filter(
                ep => ep.permission === permission
            )
        )
        .flat();

    if (isAccountManager(user) && !isDefined(accountId)) {
        return 'N/A';
    } else {
        let permissions: EntityPermission[] = filteredPermissions;
        if (isDefined(accountId)) {
            // Account level: Hide permissions that are assigned to other accounts
            permissions = permissions.filter(
                ep => !isDefined(ep.accountId) || ep.accountId === accountId
            );
        }
        return (
            distinct(
                permissions.map(
                    ep => ENTITY_PERMISSION_VALUE_TO_SHORT_NAME[ep.permission]
                )
            ).join(', ') || ''
        );
    }
}

export function getPermissionsLevel(
    user: Partial<User>
): 'Account' | 'Agency' | 'All accounts' | 'None' {
    if (isInternalUser(user)) {
        return 'All accounts';
    } else if (isAgencyManager(user)) {
        return 'Agency';
    } else if (isAccountManager(user)) {
        return 'Account';
    } else {
        return 'None'; // This should never happen, but we can handle it just in case
    }
}
