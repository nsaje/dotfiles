import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {PublisherGroupsView} from './views/publisher-groups/publisher-groups.view';
import {PublisherGroupActionsCellComponent} from './components/publisher-group-actions-cell/publisher-group-actions-cell.component';

@NgModule({
    declarations: [PublisherGroupsView, PublisherGroupActionsCellComponent],
    imports: [SharedModule],
    entryComponents: [PublisherGroupsView, PublisherGroupActionsCellComponent],
})
export class PublisherGroupsModule {}
