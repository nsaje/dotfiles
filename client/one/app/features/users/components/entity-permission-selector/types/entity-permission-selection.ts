import {EntityPermissionValue} from '../../../../../core/users/users.constants';

export type EntityPermissionSelection = {
    [key in EntityPermissionValue]?: boolean | undefined;
};
