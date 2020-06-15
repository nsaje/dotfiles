import './link-cell.component.less';
import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {LinkRendererParams} from './types/link.renderer-params';

@Component({
    templateUrl: './link-cell.component.html',
})
export class LinkCellComponent<T> implements ICellRendererAngularComp {
    params: LinkRendererParams<T>;
    text: string;
    link: string;

    agInit(params: LinkRendererParams<T>) {
        this.params = params;
        this.text = params.getText(params.data) || 'N/A';
        this.link = params.getLink(params.data);
    }

    refresh(): boolean {
        return false;
    }
}
