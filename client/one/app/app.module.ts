import {BrowserModule} from '@angular/platform-browser';
import {HttpClientXsrfModule} from '@angular/common/http';
import {UpgradeModule} from '@angular/upgrade/static';
import {ErrorHandler, NgModule} from '@angular/core';

import {APP_CONFIG} from './core/config/app.config';
import {CoreModule} from './core/core.module';
import {RavenErrorHandler} from './core/raven/raven-error-handler';
import {ViewsModule} from './views/views.module';

// Raven (Sentry) configuration
(<any>window).Raven.config( // tslint:disable-line
    'https://5443376e0b054647b8c8759811ad4d5b@sentry.io/147373',
    {
        shouldSendCallback: () => APP_CONFIG.env.prod,
    }
)
.addPlugin((<any>window).Raven.Plugins.Angular); // tslint:disable-line

@NgModule({
    imports: [
        BrowserModule,
        HttpClientXsrfModule.withOptions({
            cookieName: 'csrftoken',
            headerName: 'X-CSRFToken',
        }),
        UpgradeModule,
        CoreModule,
        ViewsModule,
    ],
    providers: [
        {provide: ErrorHandler, useClass: RavenErrorHandler},
        upgradeProvider('zemPermissions'),
        upgradeProvider('$location', 'ajs$location'),
    ],
})
export class AppModule {
    constructor (private upgrade: UpgradeModule) {}

    ngDoBootstrap () {
        this.upgrade.bootstrap(document.body, ['one'], {strictDi: true});
    }
}

function upgradeProvider (ajsName: string, name?: string): any {
    return {
        provide: name || ajsName,
        useFactory: (i: any) => i.get(ajsName),
        deps: ['$injector'],
    };
}
