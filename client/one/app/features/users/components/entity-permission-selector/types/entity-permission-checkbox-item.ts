import {EntityPermissionValue} from '../../../../../core/users/users.constants';

export interface EntityPermissionCheckboxItem {
    value: EntityPermissionValue;
    displayValue: string;
    selected: boolean | undefined;
    disabled?: boolean | undefined;
    hidden?: boolean | undefined;
    description: string;
}
