import {User} from '../../../core/users/types/user';
import {isNotEmpty} from '../../../shared/helpers/common.helpers';
import {EntityPermission} from '../../../core/users/types/entity-permission';

export function isAccountManager(user: Partial<User>): boolean {
    return (user?.entityPermissions || []).some(
        ep => isNotEmpty(ep.accountId) && ep.permission === 'read'
    );
}

export function isAgencyManager(user: Partial<User>): boolean {
    return (user?.entityPermissions || []).some(
        ep => isNotEmpty(ep.agencyId) && ep.permission === 'read'
    );
}

export function isInternalUser(user: Partial<User>): boolean {
    return (user?.entityPermissions || []).some(
        ep =>
            !isNotEmpty(ep.agencyId) &&
            !isNotEmpty(ep.accountId) &&
            ep.permission === 'read'
    );
}

export function getHighestLevelEntityPermissions(
    user: Partial<User>
): EntityPermission[] {
    // Sometimes in the DB we have users with mixed levels of entity permissions, here we remove all but the top level with read permission
    if (isInternalUser(user)) {
        return (user?.entityPermissions || []).filter(
            ep => !isNotEmpty(ep.agencyId) && !isNotEmpty(ep.accountId)
        );
    }
    if (isAgencyManager(user)) {
        return (user?.entityPermissions || []).filter(ep =>
            isNotEmpty(ep.agencyId)
        );
    }
    if (isAccountManager(user)) {
        return (user?.entityPermissions || []).filter(ep =>
            isNotEmpty(ep.accountId)
        );
    }

    return [];
}
