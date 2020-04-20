import {ICellRendererParams} from 'ag-grid-community';
import {PublisherGroupsView} from '../views/publisher-groups/publisher-groups.view';
import {PublisherGroup} from '../../../core/publisher-groups/types/publisher-group';

export interface PublisherGroupRendererParams extends ICellRendererParams {
    context: {
        componentParent: PublisherGroupsView;
    };
    data: PublisherGroup;
}
