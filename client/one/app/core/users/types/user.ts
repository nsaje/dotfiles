import {EntityPermission} from './entity-permission';

export interface User {
    id?: string;
    email: string;
    firstName?: string;
    lastName?: string;
    entityPermissions: EntityPermission[];
}
