import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {PublisherGroupsComponent} from './components/publisher-groups/publisher-groups.component';
import {PublisherGroupsLibraryView} from './views/publisher-groups-library/publisher-groups-library.view';

@NgModule({
    declarations: [PublisherGroupsComponent, PublisherGroupsLibraryView],
    imports: [SharedModule],
    entryComponents: [PublisherGroupsLibraryView],
})
export class PublisherGroupsLibraryModule {}
