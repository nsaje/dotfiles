import './pinned-row-cell.component.less';
import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {PinnedRowRendererParams} from './types/pinned-row.renderer-params';

@Component({
    templateUrl: './pinned-row-cell.component.html',
})
export class PinnedRowCellComponent implements ICellRendererAngularComp {
    params: PinnedRowRendererParams;

    agInit(params: PinnedRowRendererParams): void {
        this.params = params;
    }

    refresh(): boolean {
        return false;
    }
}
