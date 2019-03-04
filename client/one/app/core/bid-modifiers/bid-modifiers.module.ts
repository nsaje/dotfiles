import {NgModule} from '@angular/core';
import {BidModifiersService} from './services/bid-modifiers.service';
import {BidModifiersEndpoint} from './services/bid-modifiers.endpoint';

@NgModule({
    providers: [BidModifiersService, BidModifiersEndpoint],
})
export class BidModifiersModule {}
