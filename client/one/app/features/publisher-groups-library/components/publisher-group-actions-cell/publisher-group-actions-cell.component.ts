import './publisher-group-actions-cell.component.less';

import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {PublisherGroup} from '../../../../core/publisher-groups/types/publisher-group';

@Component({
    templateUrl: './publisher-group-actions-cell.component.html',
})
export class PublisherGroupActionsCellComponent
    implements ICellRendererAngularComp {
    publisherGroup: PublisherGroup;
    params: any;

    agInit(params: any) {
        this.params = params;
        this.publisherGroup = params.data;
    }

    openEditPublisherGroupModal() {
        this.params.context.componentParent.openEditPublisherGroupModal(
            this.publisherGroup
        );
    }

    download() {
        this.params.context.componentParent.download(this.publisherGroup);
    }

    refresh(): boolean {
        return false;
    }
}
