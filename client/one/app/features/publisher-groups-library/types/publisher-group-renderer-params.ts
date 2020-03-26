import {ICellRendererParams} from 'ag-grid-community';
import {PublisherGroupsLibraryView} from '../views/publisher-groups-library/publisher-groups-library.view';
import {PublisherGroup} from '../../../core/publisher-groups/types/publisher-group';

export interface PublisherGroupRendererParams extends ICellRendererParams {
    context: {
        componentParent: PublisherGroupsLibraryView;
    };
    data: PublisherGroup;
}
