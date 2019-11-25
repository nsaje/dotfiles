import {fakeAsync, tick} from '@angular/core/testing';
import * as clone from 'clone';
import {RuleEditFormStore} from './rule-edit-form.store';
import {RulesService} from '../../../../../core/rules/services/rules.service';
import {Rule} from '../../../../../core/rules/types/rule';
import {
    TimeRange,
    RuleNotificationType,
} from '../../../../../core/rules/rules.constants';

describe('RulesLibraryStore', () => {
    let rulesServiceStub: jasmine.SpyObj<RulesService>;

    let store: RuleEditFormStore;
    let mockedAgencyId: string;
    let mockedAdGroupId: string;
    let mockedRule: Rule;

    beforeEach(() => {
        rulesServiceStub = jasmine.createSpyObj(RulesService.name, ['save']);

        store = new RuleEditFormStore(rulesServiceStub);

        mockedAgencyId = '123';
        mockedAdGroupId = '12345';
        mockedRule = {
            id: null,
            name: null,
            entities: {},
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
    });

    it('should correctly initialize store', fakeAsync(() => {
        store.initStore(mockedAgencyId, mockedAdGroupId);
        tick();

        const mockedNewRule = clone(mockedRule);
        mockedNewRule.entities = {
            adGroup: {
                included: [mockedAdGroupId],
            },
        };

        expect(store.state.agencyId).toEqual(mockedAgencyId);
        expect(store.state.rule).toEqual(mockedNewRule);
        expect(store.state.availableActions).toEqual([]);
        expect(store.state.availableConditions).toEqual([]);
        expect(store.state.fieldErrors).toEqual(null);
        expect(store.state.requests).toEqual({save: {}});
    }));
});
