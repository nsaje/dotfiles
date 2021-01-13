import {NgModule} from '@angular/core';
import {CreativesEndpoint} from './services/creatives.endpoint';
import {CreativesService} from './services/creatives.service';

@NgModule({
    providers: [CreativesEndpoint, CreativesService],
})
export class CreativesModule {}
