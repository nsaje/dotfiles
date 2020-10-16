import {Rule} from '../../../../../core/rules/types/rule';
import {Account} from '../../../../../core/entities/types/account/account';
import {RuleConditionConfig} from '../../../../../core/rules/types/rule-condition-config';
import {
    TimeRange,
    RuleNotificationType,
} from '../../../../../core/rules/rules.constants';
import {RequestState} from '../../../../../shared/types/request-state';
import {RulesEditFormStoreFieldsErrorsState} from './rule-edit-form.fields-errors-state';
import {PublisherGroup} from '../../../../../core/publisher-groups/types/publisher-group';
import {ScopeSelectorState} from '../../../../../shared/components/scope-selector/scope-selector.constants';
import {EntitySelectorItem} from '../../../../../shared/components/entity-selector/types/entity-selector-item';
import {ConversionPixel} from '../../../../../core/conversion-pixels/types/conversion-pixel';

export class RuleEditFormStoreState {
    agencyId: string = null;
    accountId: string = null;
    availableConditions: RuleConditionConfig[] = [];
    availablePublisherGroups: PublisherGroup[] = [];
    availableEntities: EntitySelectorItem[] = [];
    scopeState: ScopeSelectorState = null;
    hasAgencyScope: boolean;
    isReadOnly: boolean;
    rule: Rule = {
        id: null,
        agencyId: null,
        accountId: null,
        name: null,
        entities: {
            accounts: {
                included: [],
            },
            campaigns: {
                included: [],
            },
            adGroups: {
                included: [],
            },
        },
        targetType: null,
        actionType: null,
        actionFrequency: null,
        changeStep: null,
        changeLimit: null,
        sendEmailRecipients: [],
        sendEmailSubject: null,
        sendEmailBody: null,
        publisherGroup: null,
        conditions: [],
        window: TimeRange.LastSixtyDays,
        notificationType: RuleNotificationType.None,
        notificationRecipients: [],
    };
    fieldsErrors: RulesEditFormStoreFieldsErrorsState = null;
    accounts: Account[] = [];
    availableConversionPixels: ConversionPixel[] = [];
    accountsRequests = {
        list: {} as RequestState,
    };
    campaignsRequests = {
        list: {} as RequestState,
    };
    adGroupsRequests = {
        list: {} as RequestState,
    };
    requests = {
        save: {} as RequestState,
    };
    publisherGroupsRequests = {
        search: {} as RequestState,
    };
    conversionPixelsRequests = {
        list: {} as RequestState,
    };
}
