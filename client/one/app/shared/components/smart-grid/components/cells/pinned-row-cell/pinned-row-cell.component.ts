import './pinned-row-cell.component.less';
import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {PinnedRowRendererParams} from './types/pinned-row.renderer-params';

@Component({
    templateUrl: './pinned-row-cell.component.html',
})
export class PinnedRowCellComponent implements ICellRendererAngularComp {
    params: PinnedRowRendererParams;
    value: string = '';

    agInit(params: PinnedRowRendererParams): void {
        this.params = params;
        this.value = params.formatValue(params.value);
    }

    refresh(): boolean {
        return false;
    }
}
