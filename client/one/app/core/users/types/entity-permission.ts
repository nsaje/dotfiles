import {EntityPermissionValue} from '../users.constants';

export interface EntityPermission {
    agencyId?: string;
    accountId?: string;
    permission: EntityPermissionValue;
    readonly?: boolean;
}
