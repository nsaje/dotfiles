import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {PublisherGroupsComponent} from './components/publisher-groups/publisher-groups.component';
import {PublisherGroupsLibraryView} from './views/publisher-groups-library/publisher-groups-library.view';
import {PublisherGroupsScopeSelectorComponent} from './components/publisher-groups-scope-selector/publisher-groups-scope-selector.component';
import {PublisherGroupActionsCellComponent} from './components/publisher-group-actions-cell/publisher-group-actions-cell.component';
import {PublisherGroupEditFormComponent} from './components/publisher-group-edit-form/publisher-group-edit-form.component';

@NgModule({
    declarations: [
        PublisherGroupsComponent,
        PublisherGroupsLibraryView,
        PublisherGroupsScopeSelectorComponent,
        PublisherGroupActionsCellComponent,
        PublisherGroupEditFormComponent,
    ],
    imports: [SharedModule],
    entryComponents: [
        PublisherGroupsLibraryView,
        PublisherGroupsScopeSelectorComponent,
        PublisherGroupActionsCellComponent,
    ],
})
export class PublisherGroupsLibraryModule {}
