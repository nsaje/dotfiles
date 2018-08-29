import {NgModule, Optional, SkipSelf} from '@angular/core';
import {throwIfAlreadyLoaded} from './core.module.guard';
import {MulticurrencyService} from './services/multicurrency.service';

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
        throwIfAlreadyLoaded(parentModule, CoreModule.name);
    }
}
