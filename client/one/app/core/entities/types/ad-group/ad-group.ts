import {
    AdGroupState,
    BiddingType,
    DeliveryType,
} from '../../../../app.constants';
import {AdGroupDayparting} from './ad-group-dayparting';
import {AdGroupAutopilot} from './ad-group-autopilot';
import {AdGroupTargetings} from './ad-group-targetings';

export interface AdGroup {
    id: string;
    campaignId: string;
    name: string;
    biddingType: BiddingType;
    state: AdGroupState;
    archived: boolean;
    startDate: Date;
    endDate: Date;
    redirectPixelUrls: string[];
    redirectJavascript: string;
    trackingCode: string;
    maxCpc: string;
    maxCpm: string;
    deliveryType: DeliveryType;
    clickCappingDailyAdGroupMaxClicks: number;
    dayparting: AdGroupDayparting;
    targeting: AdGroupTargetings;
    autopilot: AdGroupAutopilot;
    manageRtbSourcesAsOne: boolean;
    frequencyCapping: number;
    notes: string;
}
