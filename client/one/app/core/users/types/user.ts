import {EntityPermission} from './entity-permission';

export interface User {
    id?: number;
    email: string;
    firstName?: string;
    lastName?: string;
    entityPermissions: EntityPermission[];
}
