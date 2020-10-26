import './pinned-row-cell.component.less';
import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {PinnedRowRendererParams} from './types/pinned-row.renderer-params';
import {DEFAULT_PINNED_ROW_PARAMS} from './pinned-row-cell.component.config';
import {CellRole} from '../../../smart-grid.component.constants';

@Component({
    templateUrl: './pinned-row-cell.component.html',
})
export class PinnedRowCellComponent implements ICellRendererAngularComp {
    params: PinnedRowRendererParams;
    CellRole = CellRole;

    agInit(params: PinnedRowRendererParams): void {
        this.params = {
            ...DEFAULT_PINNED_ROW_PARAMS,
            ...params,
        };
    }

    refresh(): boolean {
        return false;
    }
}
