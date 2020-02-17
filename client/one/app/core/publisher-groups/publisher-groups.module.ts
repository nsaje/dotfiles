import {NgModule} from '@angular/core';
import {PublisherGroupsEndpoint} from './services/publisher-groups.endpoint';
import {PublisherGroupsService} from './services/publisher-groups.service';

@NgModule({
    providers: [PublisherGroupsEndpoint, PublisherGroupsService],
})
export class PublisherGroupsModule {}
