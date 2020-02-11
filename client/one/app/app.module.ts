import {BrowserModule} from '@angular/platform-browser';
import {HttpClientXsrfModule} from '@angular/common/http';
import {UpgradeModule} from '@angular/upgrade/static';
import {ErrorHandler, NgModule, DoBootstrap} from '@angular/core';

import {APP_CONFIG} from './app.config';
import {CoreModule} from './core/core.module';
import {RavenErrorHandler} from './core/handlers/raven-error.handler';
import {HeaderComponent} from './components/header/header.component';
import {FilterSelectorComponent} from './components/filter-selector/filter-selector.component';
import {FooterComponent} from './components/footer/footer.component';
import {SidebarComponent} from './components/sidebar/sidebar.component';
import {SidebarContainerComponent} from './components/sidebar-container/sidebar-container.component';
import {MainContainerComponent} from './components/main-container/main-container.component';
import {HistoryComponent} from './components/history/history.component';
import {InventoryPlanningModule} from './features/inventory-planning/inventory-planning.module';
import {EntityManagerModule} from './features/entity-manager/entity-manager.module';
import {AnalyticsModule} from './features/analytics/analytics.module';
import {RulesLibraryModule} from './features/rules-library/rules-library.module';
import {DealsLibraryModule} from './features/deals-library/deals-library.module';
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';
import {ToastrModule} from 'ngx-toastr';
import {CreditsLibraryModule} from './features/credits-library/credits-library.module';
import {ErrorForbiddenView} from './views/error-forbidden/error-forbidden.view';
import {PixelsLibraryModule} from './features/pixels-library/pixels-library.module';

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
    declarations: [
        HeaderComponent,
        FilterSelectorComponent,
        FooterComponent,
        SidebarComponent,
        SidebarContainerComponent,
        MainContainerComponent,
        HistoryComponent,
        ErrorForbiddenView,
    ],
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
            positionClass: 'toast-bottom-right',
            toastClass: 'ngx-toastr zem-toastr',
            preventDuplicates: true,
        }),

        CoreModule,

        // Feature modules
        InventoryPlanningModule,
        EntityManagerModule,
        AnalyticsModule,
        RulesLibraryModule,
        DealsLibraryModule,
        CreditsLibraryModule,
        PixelsLibraryModule,
    ],
    entryComponents: [MainContainerComponent, ErrorForbiddenView],
    providers: [
        {provide: ErrorHandler, useClass: RavenErrorHandler},
        upgradeProvider('$rootScope', 'ajs$rootScope'),
        upgradeProvider('$state', 'ajs$state'),
        upgradeProvider('$location', 'ajs$location'),
        upgradeProvider('zemPermissions'),
        upgradeProvider('zemNavigationNewService'),
    ],
})
export class AppModule implements DoBootstrap {
    constructor(private upgrade: UpgradeModule) {}

    ngDoBootstrap() {
        this.upgrade.bootstrap(document.body, ['one'], {strictDi: true});
    }
}

function upgradeProvider(ajsName: string, name?: string): any {
    return {
        provide: name || ajsName,
        useFactory: (i: any) => i.get(ajsName),
        deps: ['$injector'],
    };
}
