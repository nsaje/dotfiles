import posthog from 'posthog-js';
import {Injectable} from '@angular/core';

import {APP_CONFIG} from '../../app.config';

@Injectable()
export class PosthogService {
    init() {
        if (
            window.location.href.includes('127.0.0.1') ||
            window.location.href.includes('localhost')
        ) {
            return;
        }
        posthog.init(APP_CONFIG.posthogKey, {
            api_host: window.location.href,
        });
    }
}
