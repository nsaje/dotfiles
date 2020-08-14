import {User} from '../../../../../core/users/types/user';
import {DisplayedEntityPermissionValue} from '../../../types/displayed-entity-permission-value';
import {EntityPermission} from '../../../../../core/users/types/entity-permission';
import {
    isDefined,
    isNotEmpty,
} from '../../../../../shared/helpers/common.helpers';
import {distinct} from '../../../../../shared/helpers/array.helpers';
import {ENTITY_PERMISSION_VALUE_TO_SHORT_NAME} from '../../../users.config';

export function getPermissionsText(
    user: User,
    accountId: string,
    permissionsInColumn: DisplayedEntityPermissionValue[]
): string {
    const filteredPermissions: EntityPermission[] = permissionsInColumn
        .map(permission =>
            (user.entityPermissions || []).filter(
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
        return distinct(
            permissions.map(
                ep => ENTITY_PERMISSION_VALUE_TO_SHORT_NAME[ep.permission]
            )
        ).join(', ');
    }
}

export function isAccountManager(user: Partial<User>): boolean {
    return user.entityPermissions.some(ep => isNotEmpty(ep.accountId));
}
