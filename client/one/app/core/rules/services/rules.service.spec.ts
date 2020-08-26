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
    RuleHistoryStatus,
    RuleState,
} from '../rules.constants';
import {fakeAsync, tick} from '@angular/core/testing';
import * as clone from 'clone';
import {RuleHistory} from '../types/rule-history';

describe('RulesService', () => {
    let service: RulesService;
    let rulesEndpointStub: jasmine.SpyObj<RulesEndpoint>;
    let requestStateUpdater: RequestStateUpdater;

    let mockedRule: Rule;
    let mockedRules: Rule[];
    let mockedAgencyId: string;
    let mockedAccountId: string;
    let mockedRulesHistories: RuleHistory[];

    beforeEach(() => {
        rulesEndpointStub = jasmine.createSpyObj(RulesEndpoint.name, [
            'list',
            'create',
            'get',
            'edit',
            'listHistories',
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
                window: TimeRange.LastSixtyDays,
                notificationType: RuleNotificationType.OnRuleRun,
                notificationRecipients: ['test@test.com'],
                conditions: [],
            },
        ];
        mockedRule = clone(mockedRules[0]);

        mockedRulesHistories = [
            {
                id: '10000000',
                createdDt: new Date(),
                status: RuleHistoryStatus.SUCCESS,
                changes: '',
                changesText: '',
                changesFormatted: '',
                ruleId: '10000000',
                ruleName: 'Test rule',
                adGroupId: '1234',
                adGroupName: 'Test Ad Group',
            },
        ];
    });

    it('should list rules via endpoint', () => {
        const limit = 10;
        const offset = 0;
        const keyword = '';
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
                keyword,
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
            keyword,
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

    it('should archive rule', fakeAsync(() => {
        const mockedArchivedRule = {...mockedRule, archived: true};
        rulesEndpointStub.edit.and
            .returnValue(of(mockedArchivedRule, asapScheduler))
            .calls.reset();

        const mockedRuleId = mockedRule.id;
        service.archive(mockedRuleId, requestStateUpdater).subscribe(rule => {
            expect(rule).toEqual(mockedArchivedRule);
        });
        tick();

        expect(rulesEndpointStub.edit).toHaveBeenCalledTimes(1);
        expect(rulesEndpointStub.edit).toHaveBeenCalledWith(
            {id: mockedRuleId, archived: true},
            requestStateUpdater
        );
    }));

    it('should enable rule', fakeAsync(() => {
        const mockedEnabledRule = {...mockedRule, state: RuleState.ENABLED};
        rulesEndpointStub.edit.and
            .returnValue(of(mockedEnabledRule, asapScheduler))
            .calls.reset();

        const mockedRuleId = mockedRule.id;
        service.enable(mockedRuleId, requestStateUpdater).subscribe(rule => {
            expect(rule).toEqual(mockedEnabledRule);
        });
        tick();

        expect(rulesEndpointStub.edit).toHaveBeenCalledTimes(1);
        expect(rulesEndpointStub.edit).toHaveBeenCalledWith(
            {id: mockedRuleId, state: RuleState.ENABLED},
            requestStateUpdater
        );
    }));

    it('should pause rule', fakeAsync(() => {
        const mockedPausedRule = {...mockedRule, state: RuleState.PAUSED};
        rulesEndpointStub.edit.and
            .returnValue(of(mockedPausedRule, asapScheduler))
            .calls.reset();

        const mockedRuleId = mockedRule.id;
        service.pause(mockedRuleId, requestStateUpdater).subscribe(rule => {
            expect(rule).toEqual(mockedPausedRule);
        });
        tick();

        expect(rulesEndpointStub.edit).toHaveBeenCalledTimes(1);
        expect(rulesEndpointStub.edit).toHaveBeenCalledWith(
            {id: mockedRuleId, state: RuleState.PAUSED},
            requestStateUpdater
        );
    }));

    it('should list rules histories via endpoint', () => {
        const limit = 10;
        const offset = 0;
        rulesEndpointStub.listHistories.and
            .returnValue(of(mockedRulesHistories, asapScheduler))
            .calls.reset();

        service
            .listHistories(
                mockedAgencyId,
                mockedAccountId,
                offset,
                limit,
                null,
                null,
                null,
                null,
                null,
                requestStateUpdater
            )
            .subscribe(rulesHistories => {
                expect(rulesHistories).toEqual(mockedRulesHistories);
            });
        expect(rulesEndpointStub.listHistories).toHaveBeenCalledTimes(1);
        expect(rulesEndpointStub.listHistories).toHaveBeenCalledWith(
            mockedAgencyId,
            mockedAccountId,
            offset,
            limit,
            null,
            null,
            null,
            null,
            null,
            requestStateUpdater
        );
    });
});
