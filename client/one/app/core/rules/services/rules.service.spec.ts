import {asapScheduler, of} from 'rxjs';
import {RulesEndpoint} from './rules.endpoint';
import {RulesService} from './rules.service';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {Rule} from '../types/rule';
import {
    RuleTargetType,
    RuleActionType,
    TimeRange,
    RuleActionFrequency,
    RuleNotificationType,
} from '../rules.constants';
import {fakeAsync, tick} from '@angular/core/testing';
import * as clone from 'clone';

describe('RulesService', () => {
    let service: RulesService;
    let rulesEndpointStub: jasmine.SpyObj<RulesEndpoint>;
    let requestStateUpdater: RequestStateUpdater;

    let mockedRule: Rule;
    let mockedRules: Rule[];
    let mockedAgencyId: string;

    beforeEach(() => {
        rulesEndpointStub = jasmine.createSpyObj(RulesEndpoint.name, [
            'create',
        ]);
        service = new RulesService(rulesEndpointStub);

        requestStateUpdater = (requestName, requestState) => {};

        mockedAgencyId = '71';
        mockedRules = [
            {
                id: '10000000',
                name: 'Test rule',
                entities: {},
                targetType: RuleTargetType.AdGroupPublisher,
                actionType: RuleActionType.IncreaseBidModifier,
                actionFrequency: RuleActionFrequency.Day1,
                changeStep: null,
                changeLimit: null,
                sendEmailRecipients: [],
                sendEmailSubject: null,
                sendEmailBody: null,
                publisherGroupId: null,
                window: TimeRange.Lifetime,
                notificationType: RuleNotificationType.OnRuleRun,
                notificationRecipients: ['test@test.com'],
                conditions: [],
            },
        ];
        mockedRule = clone(mockedRules[0]);
    });

    it('should create a new rule', fakeAsync(() => {
        rulesEndpointStub.create.and
            .returnValue(of(mockedRule, asapScheduler))
            .calls.reset();

        const mockedNewRule = clone(mockedRule);
        mockedNewRule.id = null;
        service
            .save(mockedAgencyId, mockedNewRule, requestStateUpdater)
            .subscribe(rule => expect(rule).toEqual(mockedRule));
        tick();

        expect(rulesEndpointStub.create).toHaveBeenCalledTimes(1);
        expect(rulesEndpointStub.create).toHaveBeenCalledWith(
            mockedAgencyId,
            mockedNewRule,
            requestStateUpdater
        );
    }));
});
