import {Injectable, Inject} from '@angular/core';

import {APP_CONSTANTS, CampaignType} from '../../app.constants';
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

    logCampaignTypeSelection(campaignType: number | CampaignType) {
        if (!(<any>window).mixpanel) {
            return;
        }

        const accountId: number = (
            this.zemNavigationNewService.getActiveAccount() || {}
        ).id;

        let type = 'unknown';
        switch (campaignType) {
            case APP_CONSTANTS.campaignTypes.CONTENT:
            case CampaignType.CONTENT:
                type = 'content';
                break;
            case APP_CONSTANTS.campaignTypes.VIDEO:
            case CampaignType.VIDEO:
                type = 'video';
                break;
            case APP_CONSTANTS.campaignTypes.CONVERSION:
            case CampaignType.CONVERSION:
                type = 'conversion';
                break;
            case APP_CONSTANTS.campaignTypes.MOBILE:
            case CampaignType.MOBILE:
                type = 'mobile';
                break;
            case APP_CONSTANTS.campaignTypes.DISPLAY:
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
