import './deal-actions-cell.component.less';

import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {Deal} from '../../../../core/deals/types/deal';
import {DealRendererParams} from '../../types/deal.renderer-params';

@Component({
    templateUrl: './deal-actions-cell.component.html',
})
export class DealActionsCellComponent implements ICellRendererAngularComp {
    params: DealRendererParams;
    deal: Deal;
    isReadOnly: boolean;

    agInit(params: DealRendererParams) {
        this.params = params;
        this.deal = params.data;

        this.isReadOnly = this.params.context.componentParent.store.isReadOnly(
            this.deal
        );
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
