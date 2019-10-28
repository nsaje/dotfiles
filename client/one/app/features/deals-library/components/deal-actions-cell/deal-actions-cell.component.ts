import './deal-actions-cell.component.less';

import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {Deal} from '../../../../core/deals/types/deal';

@Component({
    templateUrl: './deal-actions-cell.component.html',
})
export class DealActionsCellComponent implements ICellRendererAngularComp {
    deal: Deal;
    params: any;

    agInit(params: any) {
        this.params = params;
        this.deal = params.data;
    }

    removeDeal() {
        this.params.context.componentParent.removeDeal(this.deal);
    }

    openEditDealModal() {
        this.params.context.componentParent.openEditDealModal(this.deal);
    }

    refresh(): boolean {
        return false;
    }
}
