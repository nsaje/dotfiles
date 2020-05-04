import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {PublisherGroupsView} from './views/publisher-groups/publisher-groups.view';
import {PublisherGroupActionsCellComponent} from './components/publisher-group-actions-cell/publisher-group-actions-cell.component';
import {PublisherGroupEditFormComponent} from './components/publisher-group-edit-form/publisher-group-edit-form.component';

@NgModule({
    declarations: [
        PublisherGroupsView,
        PublisherGroupActionsCellComponent,
        PublisherGroupEditFormComponent,
    ],
    imports: [SharedModule],
    entryComponents: [PublisherGroupsView, PublisherGroupActionsCellComponent],
})
export class PublisherGroupsModule {}
