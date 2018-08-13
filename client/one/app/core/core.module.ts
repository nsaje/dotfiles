import {NgModule, Optional, SkipSelf} from '@angular/core';

import {throwIfAlreadyLoaded} from './module-import-guard';
import {MulticurrencyService} from './multicurrency/multicurrency.service';

@NgModule({
    exports: [],
    declarations: [],
    providers: [MulticurrencyService],
})
export class CoreModule {
    constructor(
        @Optional()
        @SkipSelf()
        parentModule: CoreModule
    ) {
        throwIfAlreadyLoaded(parentModule, 'CoreModule');
    }
}
