import {NgModule} from '@angular/core';

import {SharedModule} from '../../../shared/shared.module';
import {FetchCreativesActionEffect} from './services/creatives-store/effects/fetch-creatives.effect';

@NgModule({
    declarations: [],
    imports: [SharedModule],
    entryComponents: [],
    providers: [FetchCreativesActionEffect],
})
export class CreativesSharedModule {}
