import './switch-button-cell.component.less';
import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {SwitchButtonRendererParams} from './types/switch-button.renderer-params';

@Component({
    templateUrl: './switch-button-cell.component.html',
})
export class SwitchButtonCellComponent<T, S>
    implements ICellRendererAngularComp {
    params: SwitchButtonRendererParams<T, S>;
    componentParent: S;
    item: T;
    value: boolean;

    agInit(params: SwitchButtonRendererParams<T, S>) {
        this.params = params;
        this.item = params.data;
        this.componentParent = params.context.componentParent;
        this.value = params.getSwitchValue(params.data);
    }

    toggle() {
        this.params.toggle(this.componentParent, this.item, !this.value);
    }

    refresh(): boolean {
        return false;
    }
}
