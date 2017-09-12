import {ErrorHandler, NgModule} from '@angular/core';
import {APP_CONFIG} from './core/config/app.config';
import {BrowserModule} from '@angular/platform-browser';
import {CoreModule} from './core/core.module';
import {RavenErrorHandler} from './core/raven/raven-error-handler';
import {SharedModule} from './shared/shared.module';
import {UpgradeModule} from '@angular/upgrade/static';

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
        UpgradeModule,
        CoreModule,
        SharedModule,
    ],
    providers: [
        {provide: ErrorHandler, useClass: RavenErrorHandler},
    ],
})
export class AppModule {
    constructor (private upgrade: UpgradeModule) {}

    ngDoBootstrap () {
        if (APP_CONFIG.env.test) {
            return; // Don't bootstrap the app while running tests
        }

        this.upgrade.bootstrap(document.body, ['one'], {strictDi: true});
    }
}
