import {EntityPermissionValue} from '../../../../../core/users/types/entity-permission-value';

export interface EntityPermissionCheckboxItem {
    value: EntityPermissionValue;
    displayValue: string;
    selected: boolean | undefined;
    disabled: boolean | undefined;
    hidden: boolean | undefined;
    description: string;
}
