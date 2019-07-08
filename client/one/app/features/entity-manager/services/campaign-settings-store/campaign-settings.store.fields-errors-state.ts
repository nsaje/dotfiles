import {FieldErrors} from '../../../../shared/types/field-errors';
import {CampaignGoalError} from '../../types/campaign-goal-error';
import {ConversionGoalError} from '../../types/conversion-goal-error';

export class CampaignSettingsStoreFieldsErrorsState {
    name: FieldErrors = [];
    goalsMissing: FieldErrors = [];
    goals: CampaignGoalError = {
        type: [] as FieldErrors[],
        value: [] as FieldErrors[],
        conversionGoal: {
            type: [] as FieldErrors[],
            conversionWindow: [] as FieldErrors[],
            goalId: [] as FieldErrors[],
        } as ConversionGoalError,
    };
}
