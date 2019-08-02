import {Injectable, Inject} from '@angular/core';
import {downgradeInjectable} from '@angular/upgrade/static';

import {APP_CONSTANTS} from '../../app.constants';
import {APP_CONFIG} from '../../app.config';

@Injectable()
export class MixpanelService {
    constructor(
        @Inject('zemNavigationNewService') private zemNavigationNewService: any
    ) {}

    init() {
        if (!(<any>window).mixpanel) {
            return;
        }

        (<any>window).mixpanel.init(APP_CONFIG.mixpanelKey);
    }

    logCampaignTypeSelection(campaignType: number) {
        if (!(<any>window).mixpanel) {
            return;
        }

        const accountId: number = (
            this.zemNavigationNewService.getActiveAccount() || {}
        ).id;

        let type = 'unknown';
        switch (campaignType) {
            case APP_CONSTANTS.campaignTypes.CONTENT:
                type = 'content';
                break;
            case APP_CONSTANTS.campaignTypes.VIDEO:
                type = 'video';
                break;
            case APP_CONSTANTS.campaignTypes.CONVERSION:
                type = 'conversion';
                break;
            case APP_CONSTANTS.campaignTypes.MOBILE:
                type = 'mobile';
                break;
            case APP_CONSTANTS.campaignTypes.DISPLAY:
                type = 'display';
                break;
        }

        (<any>window).mixpanel.track('Campaign creation', {
            accountId: accountId,
            campaignType: type,
        });
    }
}

declare var angular: angular.IAngularStatic;
angular
    .module('one.downgraded')
    .factory('zemMixpanelService', downgradeInjectable(MixpanelService));
