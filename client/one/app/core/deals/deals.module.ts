import {NgModule} from '@angular/core';
import {DealsEndpoint} from './services/deals.endpoint';
import {DealsService} from './services/deals.service';

@NgModule({
    providers: [DealsEndpoint, DealsService],
})
export class DealsModule {}
