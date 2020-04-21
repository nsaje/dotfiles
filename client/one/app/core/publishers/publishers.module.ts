import {NgModule} from '@angular/core';
import {PublishersEndpoint} from './services/publishers.endpoint';
import {PublishersService} from './services/publishers.service';

@NgModule({
    providers: [PublishersEndpoint, PublishersService],
})
export class PublishersModule {}
