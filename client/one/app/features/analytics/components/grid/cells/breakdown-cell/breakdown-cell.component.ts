import './breakdown-cell.component.less';

import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {BreakdownRendererParams} from './types/breakdown.renderer-params';

@Component({
    templateUrl: './breakdown-cell.component.html',
})
export class BreakdownCellComponent implements ICellRendererAngularComp {
    params: BreakdownRendererParams;
    valueFormatted: string;
    popoverTooltip: string;

    agInit(params: BreakdownRendererParams): void {
        this.params = params;
        this.valueFormatted = this.params.valueFormatted;
        this.popoverTooltip = this.params.getPopoverTooltip(this.params);
    }

    refresh(params: BreakdownRendererParams): boolean {
        if (this.valueFormatted !== params.valueFormatted) {
            return false;
        }
        return true;
    }
}
