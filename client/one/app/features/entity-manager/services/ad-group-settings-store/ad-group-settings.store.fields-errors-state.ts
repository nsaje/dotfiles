import {FieldErrors} from '../../../../shared/types/field-errors';
import {DealErrors} from '../../types/deal-errors';
import {NonFieldErrors} from '../../../../shared/types/non-field-errors';
import {DeviceTargetingOsErrors} from './device-targeting-os-errors';

export class AdGroupSettingsStoreFieldsErrorsState {
    name: FieldErrors = [];
    startDate: FieldErrors = [];
    endDate: FieldErrors = [];
    trackingCode: FieldErrors = [];
    biddingType: FieldErrors = [];
    bid: FieldErrors = [];
    deliveryType: FieldErrors = [];
    clickCappingDailyAdGroupMaxClicks: FieldErrors = [];
    dayparting: FieldErrors = [];
    autopilot = {
        state: [] as FieldErrors,
        dailyBudget: [] as FieldErrors,
        maxBid: [] as FieldErrors,
    };
    frequencyCapping: FieldErrors = [];
    deals: DealErrors[] = [];
    targeting = {
        devices: [] as FieldErrors | NonFieldErrors,
        os: [] as DeviceTargetingOsErrors[],
    };
}
