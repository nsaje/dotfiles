import {
    AdGroupState,
    BiddingType,
    DeliveryType,
} from '../../../../app.constants';
import {AdGroupDayparting} from './ad-group-dayparting';
import {AdGroupAutopilot} from './ad-group-autopilot';
import {AdGroupTargetings} from './ad-group-targetings';

export interface AdGroup {
    id: number;
    campaignId: number;
    name: string;
    biddingType?: BiddingType;
    state?: AdGroupState;
    archived?: boolean;
    startDate?: Date;
    endDate?: Date;
    trackingCode?: string;
    maxCpc?: string;
    maxCpm?: string;
    dailyBudget?: string;
    deliveryType?: DeliveryType;
    clickCappingDailyAdGroupMaxClicks?: number;
    clickCappingDailyClickBudget?: string;
    dayparting?: AdGroupDayparting;
    targeting?: AdGroupTargetings;
    autopilot?: AdGroupAutopilot;
    frequencyCapping?: number;
}
