import * as posthog from 'posthog-js';
import {Injectable} from '@angular/core';

import {APP_CONFIG} from '../../app.config';
import {AuthStore} from '../auth/services/auth.store';

@Injectable()
export class PosthogService {
    constructor(private authStore: AuthStore) {}
    init() {
        if (!APP_CONFIG.env.prod) {
            return;
        }
        (posthog as any).init(APP_CONFIG.posthogKey, {
            api_host: APP_CONFIG.posthogApiHost,
            loaded: () => {
                (posthog as any).identify(this.authStore.getCurrentUserId());
            },
        });
    }
}
