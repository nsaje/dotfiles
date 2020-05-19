import {NgModule} from '@angular/core';
import {CreditsService} from './services/credits.service';
import {CreditsEndpoint} from './services/credits.endpoint';

@NgModule({
    providers: [CreditsService, CreditsEndpoint],
})
export class CreditsModule {}
