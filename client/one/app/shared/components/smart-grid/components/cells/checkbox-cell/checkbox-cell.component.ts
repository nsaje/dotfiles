import './checkbox-cell.component.less';

import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {CheckboxRendererParams} from './types/checkbox.renderer-params';

@Component({
    templateUrl: './checkbox-cell.component.html',
})
export class CheckboxCellComponent implements ICellRendererAngularComp {
    params: CheckboxRendererParams;

    isChecked: boolean;
    isDisabled: boolean;

    agInit(params: CheckboxRendererParams): void {
        this.params = params;
        this.isChecked = this.params.isChecked(this.params);
        this.isDisabled = this.params.isDisabled(this.params);
    }

    refresh(params: CheckboxRendererParams): boolean {
        const isChecked = params.isChecked(this.params);
        const isDisabled = params.isDisabled(this.params);
        if (this.isChecked !== isChecked || this.isDisabled !== isDisabled) {
            return false;
        }
        return true;
    }

    setChecked($event: boolean) {
        this.params.setChecked($event, this.params);
    }
}
