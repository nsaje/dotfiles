import {EntityPermission} from './entity-permission';
import {UserStatus} from '../../../app.constants';

export interface User {
    id?: string;
    email: string;
    firstName?: string;
    lastName?: string;
    entityPermissions: EntityPermission[];
    status: UserStatus;
}
