import {EntityPermission} from './entity-permission';
import {UserStatus} from '../../../app.constants';

// TODO (msuber): add missing properties
export interface User {
    id?: string;
    email: string;
    firstName?: string;
    lastName?: string;
    entityPermissions: EntityPermission[];
    status: UserStatus;
}
