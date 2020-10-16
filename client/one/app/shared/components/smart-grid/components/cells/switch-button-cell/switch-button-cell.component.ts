import './switch-button-cell.component.less';
import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {SwitchButtonRendererParams} from './types/switch-button.renderer-params';

@Component({
    templateUrl: './switch-button-cell.component.html',
})
export class SwitchButtonCellComponent implements ICellRendererAngularComp {
    params: SwitchButtonRendererParams;
    value: boolean;
    isDisabled: boolean;

    agInit(params: SwitchButtonRendererParams): void {
        this.params = params;
        this.value = this.params.isSwitchedOn(this.params);
        this.isDisabled = this.params.isDisabled(this.params);
    }

    refresh(params: SwitchButtonRendererParams): boolean {
        const value = params.isSwitchedOn(params);
        const isDisabled = params.isDisabled(params);
        if (this.value !== value || this.isDisabled !== isDisabled) {
            return false;
        }
        return true;
    }

    toggle() {
        this.params.toggle(!this.value, this.params);
    }
}
