// Import legacy AngularJS app
import './main.ajs.js';

import {enableProdMode} from '@angular/core';
import {platformBrowserDynamic} from '@angular/platform-browser-dynamic';

import {APP_CONFIG} from './app/app.config';
import {AppModule} from './app/app.module';

if (APP_CONFIG.env.prod) {
    enableProdMode();
}

platformBrowserDynamic().bootstrapModule(AppModule);
