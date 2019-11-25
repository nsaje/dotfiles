import {Rule} from '../../../../../core/rules/types/rule';
import {RuleActionConfig} from '../../../../../core/rules/types/rule-action-config';
import {RuleConditionConfig} from '../../../../../core/rules/types/rule-condition-config';
import {
    TimeRange,
    RuleNotificationType,
} from '../../../../../core/rules/rules.constants';
import {RequestState} from '../../../../../shared/types/request-state';
import {RulesEditFormStoreFieldsErrorsState} from './rule-edit-form.fields-errors-state';

export class RuleEditFormStoreState {
    agencyId: string = null;
    availableActions: RuleActionConfig[] = [];
    availableConditions: RuleConditionConfig[] = [];
    fieldErrors: RulesEditFormStoreFieldsErrorsState = null;
    requests = {
        save: {} as RequestState,
    };
    rule: Rule = {
        id: null,
        name: null,
        entities: {
            adGroup: {
                included: [],
            },
        },
        targetType: null,
        actionType: null,
        actionFrequency: null,
        changeStep: null,
        changeLimit: null,
        conditions: [],
        window: TimeRange.Lifetime,
        notificationType: RuleNotificationType.None,
        notificationRecipients: [],
    };
}
