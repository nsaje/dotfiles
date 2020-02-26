import {Injectable, Inject, OnDestroy} from '@angular/core';

import {APP_CONSTANTS, CampaignType} from '../../app.constants';
import {APP_CONFIG} from '../../app.config';
import {Router, NavigationEnd} from '@angular/router';
import {Subject} from 'rxjs';
import {takeUntil, filter} from 'rxjs/operators';

@Injectable()
export class GoogleAnalyticsService implements OnDestroy {
    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        private router: Router,
        @Inject('zemNavigationNewService') private zemNavigationNewService: any
    ) {}

    init() {
        if (!(<any>window).ga) {
            return;
        }

        (<any>window).ga('create', APP_CONFIG.GAKey, 'auto');
        (<any>window).ga('send', 'pageview', this.router.url);

        this.router.events
            .pipe(takeUntil(this.ngUnsubscribe$))
            .pipe(filter(event => event instanceof NavigationEnd))
            .subscribe(() => {
                (<any>window).ga('send', 'pageview', this.router.url);
            });
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    logCampaignTypeSelection(campaignType: number | CampaignType) {
        if (!(<any>window).ga) {
            return;
        }

        const eventCategory = 'Campaign creation';

        const accountId: number = (
            this.zemNavigationNewService.getActiveAccount() || {}
        ).id;
        const eventLabel = `Account-ID:${accountId}`;

        let eventAction = 'unknown';
        switch (campaignType) {
            case APP_CONSTANTS.campaignTypes.CONTENT:
            case CampaignType.CONTENT:
                eventAction = 'content';
                break;
            case APP_CONSTANTS.campaignTypes.VIDEO:
            case CampaignType.VIDEO:
                eventAction = 'video';
                break;
            case APP_CONSTANTS.campaignTypes.CONVERSION:
            case CampaignType.CONVERSION:
                eventAction = 'conversion';
                break;
            case APP_CONSTANTS.campaignTypes.MOBILE:
            case CampaignType.MOBILE:
                eventAction = 'mobile';
                break;
            case APP_CONSTANTS.campaignTypes.DISPLAY:
            case CampaignType.DISPLAY:
                eventAction = 'display';
                break;
        }

        (<any>window).ga(
            'send',
            'event',
            eventCategory,
            eventAction,
            eventLabel
        );
    }
}
