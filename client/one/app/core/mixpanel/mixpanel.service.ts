import {Injectable, Inject} from '@angular/core';
import {downgradeInjectable} from '@angular/upgrade/static';

import {CampaignType} from '../../app.constants';
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
            case CampaignType.CONTENT:
                type = 'content';
                break;
            case CampaignType.VIDEO:
                type = 'video';
                break;
            case CampaignType.CONVERSION:
                type = 'conversion';
                break;
            case CampaignType.MOBILE:
                type = 'mobile';
                break;
            case CampaignType.DISPLAY:
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
