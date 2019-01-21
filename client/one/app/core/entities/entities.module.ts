import {NgModule} from '@angular/core';
import {AdGroupEndpoint} from './services/ad-group.endpoint';
import {AdGroupService} from './services/ad-group.service';
import {EntitiesUpdatesService} from './services/entities-updates.service';

@NgModule({
    providers: [AdGroupService, AdGroupEndpoint, EntitiesUpdatesService],
})
export class EntitiesModule {}
