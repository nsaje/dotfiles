import './submission-status-cell.component.less';

import {ICellRendererAngularComp} from 'ag-grid-angular';
import {ICellRendererParams} from 'ag-grid-community';
import {Component} from '@angular/core';
import {SubmissionStatus} from '../../grid-bridge/types/grid-row-data';
import {ContentAdApprovalStatus} from '../../../../../../app.constants';
import {GridRow} from '../../grid-bridge/types/grid-row';
import * as deepEqual from 'fast-deep-equal';
import * as commonHelpers from '../../../../../../shared/helpers/common.helpers';
import {AuthStore} from '../../../../../../core/auth/services/auth.store';

@Component({
    templateUrl: './submission-status-cell.component.html',
})
export class SubmissionStatusCellComponent implements ICellRendererAngularComp {
    items: SubmissionStatus[] = [];
    approvedItems: SubmissionStatus[] = [];
    nonApprovedItems: SubmissionStatus[] = [];
    isArchived: boolean = false;
    isSourceLinkVisible: boolean = false;
    isSourceLinkAnInternalFeature: boolean = false;

    constructor(private authStore: AuthStore) {}

    agInit(params: ICellRendererParams): void {
        this.items = (params.value as SubmissionStatus[]) || [];
        this.approvedItems = this.items.filter(
            item => item.status === ContentAdApprovalStatus.APPROVED
        );
        this.nonApprovedItems = this.items.filter(
            item => item.status !== ContentAdApprovalStatus.APPROVED
        );
        this.isArchived = this.isRowArchived(params.data as GridRow);
        this.isSourceLinkVisible = this.authStore.hasPermission(
            'zemauth.can_see_amplify_review_link'
        );
        this.isSourceLinkAnInternalFeature = this.authStore.isPermissionInternal(
            'zemauth.can_see_amplify_review_link'
        );
    }

    refresh(params: ICellRendererParams): boolean {
        const isArchived = this.isRowArchived(params.data as GridRow);
        if (
            !deepEqual(this.items, params.value) ||
            this.isArchived !== isArchived
        ) {
            return false;
        }
        return true;
    }

    private isRowArchived(row: GridRow): boolean {
        return commonHelpers.isDefined(row) ? row.data.archived : false;
    }
}
