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
    let mockedAccountId: string;

    beforeEach(() => {
        rulesEndpointStub = jasmine.createSpyObj(RulesEndpoint.name, [
            'list',
            'create',
            'get',
            'edit',
        ]);
        service = new RulesService(rulesEndpointStub);

        requestStateUpdater = (requestName, requestState) => {};

        mockedAgencyId = '71';
        mockedAccountId = '55';

        mockedRules = [
            {
                id: '10000000',
                agencyId: mockedAgencyId,
                accountId: null,
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

    it('should list rules via endpoint', () => {
        const limit = 10;
        const offset = 0;
        const agencyOnly = true;
        rulesEndpointStub.list.and
            .returnValue(of(mockedRules, asapScheduler))
            .calls.reset();

        service
            .list(
                mockedAgencyId,
                mockedAccountId,
                offset,
                limit,
                agencyOnly,
                requestStateUpdater
            )
            .subscribe(rules => {
                expect(rules).toEqual(mockedRules);
            });
        expect(rulesEndpointStub.list).toHaveBeenCalledTimes(1);
        expect(rulesEndpointStub.list).toHaveBeenCalledWith(
            mockedAgencyId,
            mockedAccountId,
            offset,
            limit,
            agencyOnly,
            requestStateUpdater
        );
    });

    it('should create new rule', fakeAsync(() => {
        rulesEndpointStub.create.and
            .returnValue(of(mockedRule, asapScheduler))
            .calls.reset();

        const mockedNewRule = clone(mockedRule);
        mockedNewRule.id = null;
        service.save(mockedNewRule, requestStateUpdater).subscribe(rule => {
            expect(rule).toEqual(mockedRule);
        });
        tick();

        expect(rulesEndpointStub.create).toHaveBeenCalledTimes(1);
        expect(rulesEndpointStub.create).toHaveBeenCalledWith(
            mockedNewRule,
            requestStateUpdater
        );
    }));

    it('should get rule via endpoint', () => {
        rulesEndpointStub.get.and
            .returnValue(of(mockedRule, asapScheduler))
            .calls.reset();

        const mockedRuleId = mockedRule.id;

        service.get(mockedRuleId, requestStateUpdater).subscribe(rule => {
            expect(rule).toEqual(mockedRule);
        });
        expect(rulesEndpointStub.get).toHaveBeenCalledTimes(1);
        expect(rulesEndpointStub.get).toHaveBeenCalledWith(
            mockedRuleId,
            requestStateUpdater
        );
    });

    it('should edit rule via endpoint', () => {
        const mockedNewRule = clone(mockedRules[0]);
        rulesEndpointStub.edit.and
            .returnValue(of(mockedRule, asapScheduler))
            .calls.reset();

        service.save(mockedNewRule, requestStateUpdater).subscribe(newDeal => {
            expect(newDeal).toEqual(mockedNewRule);
        });

        expect(rulesEndpointStub.edit).toHaveBeenCalledTimes(1);
        expect(rulesEndpointStub.edit).toHaveBeenCalledWith(
            mockedNewRule,
            requestStateUpdater
        );
    });
});
