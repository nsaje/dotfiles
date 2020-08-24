import './publisher-group-actions-cell.component.less';

import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {PublisherGroup} from '../../../../core/publisher-groups/types/publisher-group';
import {PublisherGroupRendererParams} from '../../types/publisher-group.renderer-params';
import {PublisherGroupsView} from '../../views/publisher-groups/publisher-groups.view';
@Component({
    templateUrl: './publisher-group-actions-cell.component.html',
})
export class PublisherGroupActionsCellComponent
    implements ICellRendererAngularComp {
    publisherGroup: PublisherGroup;
    parent: PublisherGroupsView;
    hasReadAccess: boolean;
    isReadOnly: boolean;

    agInit(params: PublisherGroupRendererParams) {
        this.parent = params.context.componentParent;
        this.publisherGroup = params.data;

        this.isReadOnly = params.context.componentParent.store.isReadOnly(
            this.publisherGroup
        );
        this.hasReadAccess = params.context.componentParent.store.hasReadAccess(
            this.publisherGroup
        );
    }

    openConnectionsModal() {
        this.parent.openConnectionsModal(this.publisherGroup);
    }

    openEditPublisherGroupModal() {
        this.parent.openEditPublisherGroupModal(this.publisherGroup);
    }

    download() {
        this.parent.download(this.publisherGroup);
    }

    delete() {
        this.parent.delete(this.publisherGroup);
    }

    refresh(): boolean {
        return false;
    }
}
