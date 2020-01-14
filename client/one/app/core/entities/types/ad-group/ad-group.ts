import {
    AdGroupState,
    BiddingType,
    DeliveryType,
} from '../../../../app.constants';
import {AdGroupDayparting} from './ad-group-dayparting';
import {AdGroupAutopilot} from './ad-group-autopilot';
import {AdGroupTargetings} from './ad-group-targetings';
import {Deal} from '../../../deals/types/deal';

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
    bid: string;
    deliveryType: DeliveryType;
    clickCappingDailyAdGroupMaxClicks: number;
    dayparting: AdGroupDayparting;
    deals: Deal[];
    targeting: AdGroupTargetings;
    autopilot: AdGroupAutopilot;
    manageRtbSourcesAsOne: boolean;
    frequencyCapping: number;
    notes: string;
}
