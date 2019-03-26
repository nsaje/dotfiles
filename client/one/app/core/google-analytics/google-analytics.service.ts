import {Injectable, Inject} from '@angular/core';
import {downgradeInjectable} from '@angular/upgrade/static';

import {CampaignType} from '../../app.constants';
import {APP_CONFIG} from '../../app.config';

@Injectable()
export class GoogleAnalyticsService {
    constructor(
        @Inject('ajs$rootScope') private ajs$rootScope: any,
        @Inject('ajs$location') private ajs$location: any,
        @Inject('zemNavigationNewService') private zemNavigationNewService: any
    ) {}

    init() {
        if (!(<any>window).ga) {
            return;
        }

        (<any>window).ga('create', APP_CONFIG.GAKey, 'auto');
        (<any>window).ga('send', 'pageview', this.ajs$location.path());

        this.ajs$rootScope.$on('$zemStateChangeSuccess', () => {
            (<any>window).ga('send', 'pageview', this.ajs$location.path());
        });
    }

    logCampaignTypeSelection(campaignType: number) {
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
            case CampaignType.CONTENT:
                eventAction = 'content';
                break;
            case CampaignType.VIDEO:
                eventAction = 'video';
                break;
            case CampaignType.CONVERSION:
                eventAction = 'conversion';
                break;
            case CampaignType.MOBILE:
                eventAction = 'mobile';
                break;
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

declare var angular: angular.IAngularStatic;
angular
    .module('one.downgraded')
    .factory(
        'zemGoogleAnalyticsService',
        downgradeInjectable(GoogleAnalyticsService)
    );
