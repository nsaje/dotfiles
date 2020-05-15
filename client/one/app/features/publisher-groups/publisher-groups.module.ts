import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {PublisherGroupsView} from './views/publisher-groups/publisher-groups.view';
import {PublisherGroupActionsCellComponent} from './components/publisher-group-actions-cell/publisher-group-actions-cell.component';
import {PublisherGroupConnectionsListComponent} from './components/publisher-group-connections-list/publisher-group-connections-list.component';

@NgModule({
    declarations: [
        PublisherGroupsView,
        PublisherGroupActionsCellComponent,
        PublisherGroupConnectionsListComponent,
    ],
    imports: [SharedModule],
    entryComponents: [PublisherGroupsView, PublisherGroupActionsCellComponent],
})
export class PublisherGroupsModule {}
