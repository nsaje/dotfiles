import {NgModule} from '@angular/core';
import {SourcesEndpoint} from './services/sources.endpoint';
import {SourcesService} from './services/sources.service';

@NgModule({
    providers: [SourcesEndpoint, SourcesService],
})
export class SourcesModule {}
