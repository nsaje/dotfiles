import {User} from '../../../core/users/types/user';
import {isNotEmpty} from '../../../shared/helpers/common.helpers';

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
