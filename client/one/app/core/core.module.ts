import {NgModule, Optional, SkipSelf} from '@angular/core';
import {throwIfAlreadyLoaded} from './core.module.guard';
import {MulticurrencyService} from './multicurrency/multicurrency.service';
import {GoogleAnalyticsService} from './google-analytics/google-analytics.service';
import {MixpanelService} from './mixpanel/mixpanel.service';
import {EntitiesModule} from './entities/entities.module';
import {PostAsGetRequestService} from './post-as-get-request/post-as-get-request.service';
import {HTTP_INTERCEPTORS} from '@angular/common/http';
import {ApiConverterHttpInterceptor} from './interceptors/api-converter.interceptor';
import {BidModifiersModule} from './bid-modifiers/bid-modifiers.module';

const HTTP_INTERCEPTOR_PROVIDERS = [
    {
        provide: HTTP_INTERCEPTORS,
        useClass: ApiConverterHttpInterceptor,
        multi: true,
    },
];

@NgModule({
    imports: [EntitiesModule, BidModifiersModule],
    providers: [
        GoogleAnalyticsService,
        MulticurrencyService,
        MixpanelService,
        PostAsGetRequestService,
        HTTP_INTERCEPTOR_PROVIDERS,
    ],
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
