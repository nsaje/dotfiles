import './creative-actions-cell.component.less';

import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {Creative} from '../../../../../core/creatives/types/creative';
import {CreativeRendererParams} from '../../types/creative.renderer-params';

@Component({
    templateUrl: './creative-actions-cell.component.html',
})
export class CreativeActionsCellComponent implements ICellRendererAngularComp {
    params: CreativeRendererParams;
    creative: Creative;
    isReadOnly: boolean;

    agInit(params: CreativeRendererParams) {
        this.params = params;
        this.creative = params.data;

        this.isReadOnly = this.params.context.componentParent.store.isReadOnly(
            this.creative
        );
    }

    edit() {
        // TODO
    }

    clone() {
        // TODO
    }

    exportToCsv() {
        // TODO
    }

    refresh(): boolean {
        return true;
    }
}
