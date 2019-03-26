import {NestedFieldsErrors} from '../../../shared/types/nested-fields-errors';
import {FieldErrors} from '../../../shared/types/field-errors';

export class AdGroupSettingsStoreFieldsErrorsState {
    name: FieldErrors = [];
    startDate: FieldErrors = [];
    endDate: FieldErrors = [];
    trackingCode: FieldErrors = [];
    biddingType: FieldErrors = [];
    maxCpc: FieldErrors = [];
    maxCpm: FieldErrors = [];
    deliveryType: FieldErrors = [];
    clickCappingDailyAdGroupMaxClicks: FieldErrors = [];
    clickCappingDailyClickBudget: FieldErrors = [];
    dayparting: FieldErrors = [];
    autopilot: NestedFieldsErrors = {
        state: [],
        dailyBudget: [],
    };
    frequencyCapping: FieldErrors = [];
}
