import './link-cell.component.less';
import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {LinkRendererParams} from './types/link.renderer-params';
import {LinkCellIcon} from './link-cell.component.constants';
import * as commonHelpers from '../../../../../helpers/common.helpers';

@Component({
    templateUrl: './link-cell.component.html',
})
export class LinkCellComponent<T> implements ICellRendererAngularComp {
    params: LinkRendererParams<T>;
    text: string;
    link: string;
    linkIcon: LinkCellIcon;

    agInit(params: LinkRendererParams<T>) {
        this.params = params;
        this.text = params.getText(params);
        this.link = params.getLink(params);
        if (commonHelpers.isDefined(params.getLinkIcon)) {
            this.linkIcon = params.getLinkIcon(params);
        }
    }

    refresh(params: LinkRendererParams<T>): boolean {
        const link = params.getLink(params);
        if (this.link !== link) {
            return false;
        }
        return true;
    }
}
