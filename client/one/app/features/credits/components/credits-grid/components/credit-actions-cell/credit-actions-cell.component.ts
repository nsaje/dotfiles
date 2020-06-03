import './credit-actions-cell.component.less';
import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {Credit} from '../../../../../../core/credits/types/credit';
import {CreditRendererParams} from '../../types/credit.renderer-params';
import * as commonHelpers from '../../../../../../shared/helpers/common.helpers';
import {CreditStatus} from '../../../../../../app.constants';

@Component({
    templateUrl: './credit-actions-cell.component.html',
})
export class CreditActionsCellComponent implements ICellRendererAngularComp {
    params: CreditRendererParams;
    credit: Credit;
    isReadOnly: boolean;
    isSigned: boolean;
    isCanceled: boolean;

    agInit(params: CreditRendererParams) {
        this.params = params;
        this.credit = params.data;

        this.isReadOnly =
            !this.params.context.componentParent.store.state.hasAgencyScope &&
            commonHelpers.isDefined(this.credit.agencyId);
        this.isSigned = this.credit.status === CreditStatus.SIGNED;
        this.isCanceled = this.credit.status === CreditStatus.CANCELED;
    }

    openCreditItemModal() {
        this.params.context.componentParent.openCreditItemModal(this.credit);
    }

    cancelCreditItem() {
        this.params.context.componentParent.cancelCreditItem(this.credit);
    }

    refresh(): boolean {
        return false;
    }
}
