import {NgModule, Optional, SkipSelf} from '@angular/core';
import {throwIfAlreadyLoaded} from './core.module.guard';
import {MulticurrencyService} from './multicurrency/multicurrency.service';
import {GoogleAnalyticsService} from './google-analytics/google-analytics.service';
import {MixpanelService} from './mixpanel/mixpanel.service';
import {EntitiesModule} from './entities/entities.module';

@NgModule({
    imports: [EntitiesModule],
    providers: [GoogleAnalyticsService, MulticurrencyService, MixpanelService],
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
