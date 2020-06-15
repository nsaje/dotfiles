import {NgModule, Optional, SkipSelf} from '@angular/core';
import {GoogleAnalyticsService} from './google-analytics/google-analytics.service';
import {MixpanelService} from './mixpanel/mixpanel.service';
import {EntitiesModule} from './entities/entities.module';
import {PostAsGetRequestService} from './post-as-get-request/post-as-get-request.service';
import {HTTP_INTERCEPTORS} from '@angular/common/http';
import {ApiConverterHttpInterceptor} from './interceptors/api-converter.interceptor';
import {BidModifiersModule} from './bid-modifiers/bid-modifiers.module';
import {ConversionPixelsModule} from './conversion-pixels/conversion-pixels.module';
import {DealsModule} from './deals/deals.module';
import {PublisherGroupsModule} from './publisher-groups/publisher-groups.module';
import {RulesModule} from './rules/rules.module';
import {SourcesModule} from './sources/sources.module';
import {ExceptionHttpInterceptor} from './interceptors/exception.interceptor';
import {NotificationService} from './notification/services/notification.service';
import {ExceptionHandlerService} from './exception-handler/services/exception-handler.service';
import {PublishersModule} from './publishers/publishers.module';
import {GeolocationsModule} from './geolocations/geolocations.module';
import {CreditsModule} from './credits/credits.module';
import {UsersModule} from './users/users.module';

const HTTP_INTERCEPTOR_PROVIDERS = [
    {
        provide: HTTP_INTERCEPTORS,
        useClass: ApiConverterHttpInterceptor,
        multi: true,
    },
    {
        provide: HTTP_INTERCEPTORS,
        useClass: ExceptionHttpInterceptor,
        multi: true,
    },
];

@NgModule({
    imports: [
        EntitiesModule,
        BidModifiersModule,
        ConversionPixelsModule,
        DealsModule,
        RulesModule,
        SourcesModule,
        PublisherGroupsModule,
        PublishersModule,
        GeolocationsModule,
        CreditsModule,
        UsersModule,
    ],
    providers: [
        GoogleAnalyticsService,
        MixpanelService,
        PostAsGetRequestService,
        NotificationService,
        ExceptionHandlerService,
        HTTP_INTERCEPTOR_PROVIDERS,
    ],
})
export class CoreModule {
    constructor(
        @Optional()
        @SkipSelf()
        parentModule: CoreModule
    ) {
        if (parentModule) {
            throw new Error(
                `${CoreModule.name} has already been loaded. Import ${CoreModule.name} in the AppModule only.`
            );
        }
    }
}
