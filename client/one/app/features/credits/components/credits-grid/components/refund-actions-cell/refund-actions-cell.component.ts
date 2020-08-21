import './refund-actions-cell.component.less';
import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {Credit} from '../../../../../../core/credits/types/credit';
import {CreditRendererParams} from '../../types/credit.renderer-params';
import {CreditStatus} from '../../../../../../app.constants';
import {CreditGridType} from '../../../../credits.constants';

@Component({
    templateUrl: './refund-actions-cell.component.html',
})
export class RefundActionsCellComponent implements ICellRendererAngularComp {
    params: CreditRendererParams;
    credit: Credit;
    isCanceled: boolean;
    isPast: boolean;
    isReadOnly: boolean;
    canManageRefunds: boolean;

    agInit(params: CreditRendererParams) {
        this.params = params;
        this.credit = params.data;

        this.isCanceled = this.credit.status === CreditStatus.CANCELED;
        this.isPast = this.params.creditGridType === CreditGridType.PAST;
        this.isReadOnly = this.params.context.componentParent.store.isReadOnly(
            this.credit
        );
        this.canManageRefunds = this.params.context.componentParent.authStore.hasPermission(
            'zemauth.can_manage_credit_refunds'
        );
    }

    openCreditRefundCreateModal() {
        this.params.context.componentParent.openCreditRefundCreateModal(
            this.credit
        );
    }

    openCreditRefundListModal() {
        this.params.context.componentParent.openCreditRefundListModal(
            this.credit
        );
    }

    refresh(): boolean {
        return false;
    }
}
