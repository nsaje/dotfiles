import './creative-asset-cell.component.less';

import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {Creative} from '../../../../../core/creatives/types/creative';
import {ICellRendererParams} from 'ag-grid-community';

@Component({
    templateUrl: './creative-asset-cell.component.html',
})
export class CreativeAssetCellComponent implements ICellRendererAngularComp {
    item: Creative;

    agInit(params: ICellRendererParams): void {
        this.item = params.data;
    }

    refresh(params: any): boolean {
        return false;
    }
}
