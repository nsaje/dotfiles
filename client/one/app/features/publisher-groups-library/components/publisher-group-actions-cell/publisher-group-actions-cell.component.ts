import './publisher-group-actions-cell.component.less';

import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {PublisherGroup} from '../../../../core/publisher-groups/types/publisher-group';
import {PublisherGroupRendererParams} from '../../types/publisher-group-renderer-params';
import {PublisherGroupsLibraryView} from '../../views/publisher-groups-library/publisher-groups-library.view';

@Component({
    templateUrl: './publisher-group-actions-cell.component.html',
})
export class PublisherGroupActionsCellComponent
    implements ICellRendererAngularComp {
    publisherGroup: PublisherGroup;
    parent: PublisherGroupsLibraryView;

    agInit(params: PublisherGroupRendererParams) {
        this.parent = params.context.componentParent;
        this.publisherGroup = params.data;
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
