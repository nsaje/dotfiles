import './checkbox-filter-header-cell.component.less';

import {IHeaderAngularComp} from 'ag-grid-angular';
import {Component, ViewChild} from '@angular/core';
import {CheckboxFilterHeaderParams} from './types/checkbox-filter-header-params';
import {GridSelectionCustomFilter} from '../../grid-bridge/types/grid-selection-custom-filter';
import {DropdownDirective} from '../../../../../../shared/components/dropdown/dropdown.directive';

@Component({
    templateUrl: './checkbox-filter-header-cell.component.html',
})
export class CheckboxFilterHeaderCellComponent implements IHeaderAngularComp {
    params: CheckboxFilterHeaderParams;
    isChecked: boolean;
    filters: GridSelectionCustomFilter[];

    @ViewChild(DropdownDirective, {static: false})
    filtersDropdown: DropdownDirective;

    agInit(params: CheckboxFilterHeaderParams): void {
        this.params = params;
        this.isChecked = this.params.isChecked(this.params);
        this.filters = this.params.getCustomFilters(this.params) || [];
    }

    refresh(params: CheckboxFilterHeaderParams): boolean {
        const isChecked = params.isChecked(this.params);
        if (this.isChecked !== isChecked) {
            return false;
        }
        return true;
    }

    setChecked($event: boolean) {
        this.params.setChecked($event, this.params);
    }

    setCustomFilter($event: GridSelectionCustomFilter) {
        this.filtersDropdown.close();
        this.params.setCustomFilter($event, this.params);
    }
}
