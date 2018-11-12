import {NgModule, Optional, SkipSelf} from '@angular/core';
import {throwIfAlreadyLoaded} from './core.module.guard';
import {MulticurrencyService} from './multicurrency/multicurrency.service';
import {GoogleAnalyticsService} from './google-analytics/google-analytics.service';

@NgModule({
    exports: [],
    declarations: [],
    providers: [GoogleAnalyticsService, MulticurrencyService],
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
