import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {PublisherGroupsComponent} from './components/publisher-groups/publisher-groups.component';
import {PublisherGroupsLibraryView} from './views/publisher-groups-library/publisher-groups-library.view';
import {PublisherGroupsScopeSelectorComponent} from './components/publisher-groups/publisher-groups-scope-selector.component';

@NgModule({
    declarations: [
        PublisherGroupsComponent,
        PublisherGroupsLibraryView,
        PublisherGroupsScopeSelectorComponent,
    ],
    imports: [SharedModule],
    entryComponents: [
        PublisherGroupsLibraryView,
        PublisherGroupsScopeSelectorComponent,
    ],
})
export class PublisherGroupsLibraryModule {}
