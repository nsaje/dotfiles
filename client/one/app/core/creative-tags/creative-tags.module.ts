import {NgModule} from '@angular/core';
import {CreativeTagsEndpoint} from './services/creative-tags.endpoint';
import {CreativeTagsService} from './services/creative-tags.service';

@NgModule({
    providers: [CreativeTagsEndpoint, CreativeTagsService],
})
export class CreativeTagsModule {}
