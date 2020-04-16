import {BrowserModule} from '@angular/platform-browser';
import {HttpClientXsrfModule} from '@angular/common/http';
import {UpgradeModule} from '@angular/upgrade/static';
import {ErrorHandler, NgModule} from '@angular/core';

import {APP_CONFIG} from './app.config';
import {CoreModule} from './core/core.module';
import {RavenErrorHandler} from './core/handlers/raven-error.handler';
import {InventoryPlanningModule} from './features/inventory-planning/inventory-planning.module';
import {EntityManagerModule} from './features/entity-manager/entity-manager.module';
import {AnalyticsModule} from './features/analytics/analytics.module';
import {RulesLibraryModule} from './features/rules-library/rules-library.module';
import {DealsModule} from './features/deals/deals.module';
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';
import {ToastrModule} from 'ngx-toastr';
import {CreditsModule} from './features/credits/credits.module';
import {ErrorForbiddenView} from './views/error-forbidden/error-forbidden.view';
import {PixelsLibraryModule} from './features/pixels-library/pixels-library.module';
import {UserPermissionsModule} from './features/user-permissions/user-permissions.module';
import {ScheduledReportsModule} from './features/scheduled-reports/scheduled-reports.module';
import {PublisherGroupsModule} from './features/publisher-groups/publisher-groups.module';
import {DashboardView} from './views/dashboard/dashboard.view';
import {AppRootComponent} from './app-root.component';
import {LayoutModule} from './layout/layout.module';
import {AppInitializationModule} from './app-initialization.module';
import {RouterModule, RouteReuseStrategy} from '@angular/router';
import {APP_ROUTES} from './app.routes';
import {ArchivedModule} from './features/archived/archived.module';
import {NewEntityAnalyticsMockModule} from './features/new-entity-analytics-mock/new-entity-analytics-mock.module';
import {CanActivateDashboardGuard} from './route-guards/canActivateDashboard.guard';
import {CanActivateRedirectGuard} from './route-guards/canActivateRedirect.guard';
import {SidebarContentModule} from './features/sidebar-content/sidebar-content.module';
import {CacheRouteReuseStrategy} from './route-strategy/cache.strategy';

// Raven (Sentry) configuration
if (APP_CONFIG.env.prod) {
    (<any>window).Raven.config(
        'https://5443376e0b054647b8c8759811ad4d5b@sentry.io/147373',
        {
            shouldSendCallback: () => APP_CONFIG.env.prod,
            release: APP_CONFIG.buildNumber,
        }
    )
        .addPlugin((<any>window).Raven.Plugins.Angular)
        .install();
}

@NgModule({
    declarations: [DashboardView, ErrorForbiddenView, AppRootComponent],
    imports: [
        // Angular modules
        BrowserModule,
        HttpClientXsrfModule.withOptions({
            cookieName: 'csrftoken',
            headerName: 'X-CSRFToken',
        }),
        UpgradeModule,
        BrowserAnimationsModule,

        ToastrModule.forRoot({
            enableHtml: true,
            tapToDismiss: false,
            closeButton: true,
            timeOut: 0,
            extendedTimeOut: 0,
            positionClass: 'toast-bottom-center',
            toastClass: 'ngx-toastr zem-toastr',
            preventDuplicates: true,
            maxOpened: 1,
        }),

        // Initialization module
        AppInitializationModule,

        CoreModule,

        // Feature modules
        LayoutModule,
        InventoryPlanningModule,
        EntityManagerModule,
        AnalyticsModule,
        ArchivedModule,
        RulesLibraryModule,
        DealsModule,
        CreditsModule,
        PixelsLibraryModule,
        UserPermissionsModule,
        ScheduledReportsModule,
        PublisherGroupsModule,
        SidebarContentModule,
        NewEntityAnalyticsMockModule,

        // App router
        RouterModule.forRoot(APP_ROUTES),
    ],
    providers: [
        CanActivateDashboardGuard,
        CanActivateRedirectGuard,
        {provide: ErrorHandler, useClass: RavenErrorHandler},
        {
            provide: '$scope',
            useFactory: ajs$scope,
            deps: ['$injector'],
        },
        {
            provide: 'zemPermissions',
            useFactory: ajs$zemPermissions,
            deps: ['$injector'],
        },
        {
            provide: 'zemNavigationService',
            useFactory: ajs$zemNavigationService,
            deps: ['$injector'],
        },
        {
            provide: 'zemNavigationNewService',
            useFactory: ajs$zemNavigationNewService,
            deps: ['$injector'],
        },
        {
            provide: 'zemDesignHelpersService',
            useFactory: ajs$zemDesignHelpersService,
            deps: ['$injector'],
        },
        {
            provide: 'zemInitializationService',
            useFactory: ajs$zemInitializationService,
            deps: ['$injector'],
        },
        {
            provide: RouteReuseStrategy,
            useClass: CacheRouteReuseStrategy,
        },
    ],
    bootstrap: [AppRootComponent],
})
export class AppModule {}

function ajs$scope($injector: any) {
    return $injector.get('$rootScope');
}

function ajs$zemPermissions($injector: any) {
    return $injector.get('zemPermissions');
}

function ajs$zemNavigationService($injector: any) {
    return $injector.get('zemNavigationService');
}

function ajs$zemNavigationNewService($injector: any) {
    return $injector.get('zemNavigationNewService');
}

function ajs$zemDesignHelpersService($injector: any) {
    return $injector.get('zemDesignHelpersService');
}

function ajs$zemInitializationService($injector: any) {
    return $injector.get('zemInitializationService');
}
