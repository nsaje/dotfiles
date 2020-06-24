import {EntityPermissionValue} from '../../../../../core/users/types/entity-permission-value';

export type EntityPermissionSelection = {
    [key in EntityPermissionValue]: boolean | undefined;
};
