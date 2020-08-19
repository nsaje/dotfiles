import './entity-permission-selector.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
    OnChanges,
} from '@angular/core';
import {CheckboxSliderItem} from '../../../../shared/components/checkbox-slider/types/checkbox-slider-item';
import {EntityPermissionCheckboxItem} from './types/entity-permission-checkbox-item';
import {
    ENTITY_PERMISSION_VALUE_TO_DESCRIPTION,
    ENTITY_PERMISSION_VALUE_TO_NAME,
    GENERAL_PERMISSIONS,
    REPORTING_PERMISSIONS,
} from '../../users.config';
import {EntityPermissionSelection} from './types/entity-permission-selection';
import {DisplayedEntityPermissionValue} from '../../types/displayed-entity-permission-value';
import {EntityPermissionCheckboxStates} from './types/entity-permission-checkbox-states';
import {EntityPermissionValue} from '../../../../core/users/users.constants';

@Component({
    selector: 'zem-entity-permission-selector',
    templateUrl: './entity-permission-selector.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EntityPermissionSelectorComponent implements OnChanges {
    @Input()
    checkboxStates: EntityPermissionCheckboxStates;
    @Input()
    selection: EntityPermissionSelection;
    @Input()
    isDisabled: boolean = false;
    @Input()
    errors: string[];
    @Output()
    selectionChange: EventEmitter<EntityPermissionSelection> = new EventEmitter<
        EntityPermissionSelection
    >();

    formattedOptions: EntityPermissionCheckboxItem[] = [];
    formattedReportingOptions: CheckboxSliderItem<EntityPermissionValue>[];

    ngOnChanges(): void {
        this.formattedOptions = GENERAL_PERMISSIONS.map(
            this.getGeneralItem.bind(this)
        );
        this.formattedReportingOptions = REPORTING_PERMISSIONS.map(
            this.getReportingItem.bind(this)
        );
    }

    toggleOption(option: EntityPermissionCheckboxItem) {
        const newSelection: EntityPermissionSelection = {...this.selection};
        newSelection[option.value] = this.selection[option.value] !== true;

        this.selectionChange.emit(newSelection);
    }

    toggleReportingOptions(
        $event: CheckboxSliderItem<DisplayedEntityPermissionValue>[]
    ) {
        const newSelection: EntityPermissionSelection = {...this.selection};
        $event
            .filter(item => item.value !== 'total_spend')
            .forEach(item => {
                newSelection[item.value] = item.selected;
            });

        this.selectionChange.emit(newSelection);
    }

    private getGeneralItem(
        permission: EntityPermissionValue
    ): EntityPermissionCheckboxItem {
        const isPermissionSelected: boolean = this.isPermissionSelected(
            permission
        );
        return {
            value: permission,
            displayValue: ENTITY_PERMISSION_VALUE_TO_NAME[permission],
            description: ENTITY_PERMISSION_VALUE_TO_DESCRIPTION[permission],
            selected: isPermissionSelected,
            disabled: this.checkboxStates[permission] === 'disabled',
            hidden: this.checkboxStates[permission] === 'hidden',
        };
    }

    private getReportingItem(
        permission: DisplayedEntityPermissionValue
    ): CheckboxSliderItem<DisplayedEntityPermissionValue> {
        const isPermissionSelected: boolean = this.isPermissionSelected(
            permission
        );
        return {
            value: permission,
            displayValue: ENTITY_PERMISSION_VALUE_TO_NAME[permission],
            selected: isPermissionSelected,
            disabled: this.checkboxStates[permission] === 'disabled',
            hidden: this.checkboxStates[permission] === 'hidden',
        };
    }

    private isPermissionSelected(
        permission: DisplayedEntityPermissionValue
    ): boolean | undefined {
        if (permission === 'total_spend') {
            return true; // This is not a real permission, but a dummy value
        } else {
            return this.selection ? this.selection[permission] : false;
        }
    }
}
