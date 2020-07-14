import './info-cell.component.less';
import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {InfoCellRendererParams} from './types/info-cell.renderer-params';

@Component({
    templateUrl: './info-cell.component.html',
})
export class InfoCellComponent<T, S> implements ICellRendererAngularComp {
    params: InfoCellRendererParams<T, S>;
    mainContent: string;
    info: string;

    agInit(params: InfoCellRendererParams<T, S>) {
        this.params = params;
        this.mainContent = params.getMainContent(
            params.data,
            params.context?.componentParent
        );
        this.info = params.getInfoText(
            params.data,
            params.context?.componentParent
        );
    }

    refresh(): boolean {
        return false;
    }
}
