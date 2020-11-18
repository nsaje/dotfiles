import './pinned-row-cell.component.less';
import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {PinnedRowRendererParams} from './types/pinned-row.renderer-params';
import {DEFAULT_PINNED_ROW_PARAMS} from './pinned-row-cell.component.config';
import {CellRole} from '../../../smart-grid.component.constants';
import * as commonHelpers from '../../../../../helpers/common.helpers';

@Component({
    templateUrl: './pinned-row-cell.component.html',
})
export class PinnedRowCellComponent implements ICellRendererAngularComp {
    params: PinnedRowRendererParams;
    valueFormatted: string;
    role: CellRole;
    CellRole = CellRole;

    agInit(params: PinnedRowRendererParams): void {
        this.params = {
            ...DEFAULT_PINNED_ROW_PARAMS,
            ...params,
        };
        this.valueFormatted = this.params.valueFormatted;
        this.role = commonHelpers.getValueOrDefault(
            this.params.role,
            CellRole.Dimension
        );
    }

    refresh(params: PinnedRowRendererParams): boolean {
        const valueFormatted = params.valueFormatted;
        if (this.valueFormatted !== valueFormatted) {
            return false;
        }
        return true;
    }
}
