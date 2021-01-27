import './polyfills';

// Import legacy AngularJS tests
import './main-ajs.test.js';

import 'zone.js/dist/long-stack-trace-zone';
import 'zone.js/dist/proxy';
import 'zone.js/dist/sync-test';
import 'zone.js/dist/jasmine-patch';
import 'zone.js/dist/async-test';
import 'zone.js/dist/fake-async-test';
import {getTestBed} from '@angular/core/testing';
import {
    BrowserDynamicTestingModule,
    platformBrowserDynamicTesting,
} from '@angular/platform-browser-dynamic/testing';

declare var __karma__: any;
// Prevent Karma from running prematurely
__karma__.loaded = () => {};

getTestBed().initTestEnvironment(
    BrowserDynamicTestingModule,
    platformBrowserDynamicTesting()
);

const context = require.context('./', true, /\.spec\.ts$/);
context.keys().map(context);

// Start Karma to run the tests
__karma__.start();
