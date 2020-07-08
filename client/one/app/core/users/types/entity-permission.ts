import {EntityPermissionValue} from './entity-permission-value';

export interface EntityPermission {
    agencyId?: string;
    accountId?: string;
    permission: EntityPermissionValue;
}
