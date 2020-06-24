import {EntityPermissionValue} from '../../../../../core/users/types/entity-permission-value';

export interface EntityPermissionCheckboxItem {
    value: EntityPermissionValue;
    displayValue: string;
    selected: boolean | undefined;
    description: string;
}
