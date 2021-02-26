import {NgModule} from '@angular/core';
import {EntityHistoryService} from './services/entity-history.service';
import {EntityHistoryEndpoint} from './services/entity-history.endpoint';

@NgModule({
    providers: [EntityHistoryService, EntityHistoryEndpoint],
})
export class EntityHistoryModule {}
