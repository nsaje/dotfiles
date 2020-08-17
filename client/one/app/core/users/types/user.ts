import {EntityPermission} from './entity-permission';
import {UserStatus} from '../../../app.constants';
import {Permission} from './permission';

export interface User {
    id?: string;
    email: string;
    firstName?: string;
    lastName?: string;
    name?: string;
    status: UserStatus;
    agencies?: number[];
    timezoneOffset?: number;
    intercomUserHash?: string;
    defaultCsvSeparator?: string;
    defaultCsvDecimalSeparator?: string;
    permissions?: Permission[];
    entityPermissions: EntityPermission[];
}
