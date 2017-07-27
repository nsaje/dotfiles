// Import legacy AngularJS app
import './main.ajs.js';

import {APP_CONFIG} from './app/core/config/app.config';
import {AppModule} from './app/app.module';
import {enableProdMode} from '@angular/core';
import {platformBrowserDynamic} from '@angular/platform-browser-dynamic';

if (APP_CONFIG.env.prod) {
    enableProdMode();
}

platformBrowserDynamic().bootstrapModule(AppModule);
