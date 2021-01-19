import {NgModule} from '@angular/core';
import {CreativesEndpoint} from './services/creatives.endpoint';
import {CreativesService} from './services/creatives.service';
import {CreativeTagsEndpoint} from '../creative-tags/services/creative-tags.endpoint';
import {CreativeTagsService} from '../creative-tags/services/creative-tags.service';

@NgModule({
    providers: [
        CreativesEndpoint,
        CreativesService,
        CreativeTagsEndpoint,
        CreativeTagsService,
    ],
})
export class CreativesModule {}
