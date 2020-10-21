import './actions-cell.component.less';

import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {Grid} from '../../grid-bridge/types/grid';
import {GridRow} from '../../grid-bridge/types/grid-row';
import {ActionsRendererParams} from './types/actions.renderer-params';

@Component({
    templateUrl: './actions-cell.component.html',
})
export class ActionsCellComponent implements ICellRendererAngularComp {
    params: ActionsRendererParams;
    grid: Grid;
    row: GridRow;

    agInit(params: ActionsRendererParams): void {
        this.params = params;
        this.grid = this.params.getGrid(this.params);
        this.row = this.params.getGridRow(this.params);
    }

    refresh(params: ActionsRendererParams): boolean {
        return false;
    }
}
