// Import legacy AngularJS app
import './main.ajs.js';

import {enableProdMode} from '@angular/core';
import {platformBrowser} from '@angular/platform-browser';

import {APP_CONFIG} from './app/app.config';
import {AppModule} from './app/app.module';

if (APP_CONFIG.env.prod) {
    enableProdMode();
}

// Using @angular/platform-browser instead of @angular/platform-browser-dynamic.
// This will remove the JIT compiler (2MB) from the final bundle and it will
// use AOT compiled files, included by @ngtools/webpack.
platformBrowser().bootstrapModule(AppModule);
