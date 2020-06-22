import {fakeAsync, tick} from '@angular/core/testing';
import {asapScheduler, of} from 'rxjs';
import {RulesService} from '../../../../core/rules/services/rules.service';
import {RulesHistoriesStore} from './rules-histories.store';
import {RuleHistory} from '../../../../core/rules/types/rule-history';
import {RuleHistoryStatus} from '../../../../core/rules/rules.constants';

describe('RulesHistoriesStore', () => {
    let rulesServiceStub: jasmine.SpyObj<RulesService>;
    let store: RulesHistoriesStore;
    let mockedHistories: RuleHistory[];
    let mockedAgencyId: string;
    let mockedAccountId: string;
    let mockedRuleId: string;
    let mockedAdGroupId: string;
    let mockedStartDate: Date;
    let mockedEndDate: Date;

    beforeEach(() => {
        rulesServiceStub = jasmine.createSpyObj(RulesService.name, [
            'listHistories',
        ]);
        store = new RulesHistoriesStore(rulesServiceStub);

        const date = new Date();
        mockedHistories = [
            {
                id: '10000000',
                createdDt: date,
                status: RuleHistoryStatus.SUCCESS,
                changes: '',
                changesText: '',
                ruleId: '10000000',
                ruleName: 'Test rule',
                adGroupId: '1234',
                adGroupName: 'Test Ad Group',
            },
        ];

        mockedAgencyId = '71';
        mockedAccountId = '55';
        mockedRuleId = '10000000';
        (mockedAdGroupId = '1234'), (mockedStartDate = date);
        mockedEndDate = date;
    });

    it('should correctly initialize store', fakeAsync(() => {
        rulesServiceStub.listHistories.and
            .returnValue(of(mockedHistories, asapScheduler))
            .calls.reset();
        store.setStore(
            mockedAgencyId,
            mockedAccountId,
            {
                page: 1,
                pageSize: 10,
                type: 'server',
            },
            mockedRuleId,
            mockedAdGroupId,
            mockedStartDate,
            mockedEndDate
        );
        tick();

        expect(store.state.entities).toEqual(mockedHistories);
        expect(store.state.accountId).toEqual(mockedAccountId);
        expect(store.state.agencyId).toEqual(mockedAgencyId);
        expect(rulesServiceStub.listHistories).toHaveBeenCalledTimes(1);
        expect(rulesServiceStub.listHistories).toHaveBeenCalledWith(
            mockedAgencyId,
            mockedAccountId,
            0,
            10,
            mockedRuleId,
            mockedAdGroupId,
            mockedStartDate,
            mockedEndDate,
            (<any>store).requestStateUpdater
        );
    }));

    it('should list histories via service', fakeAsync(() => {
        store.state.agencyId = mockedAgencyId;
        store.state.accountId = mockedAccountId;

        rulesServiceStub.listHistories.and
            .returnValue(of(mockedHistories, asapScheduler))
            .calls.reset();
        store.loadEntities(
            {
                page: 1,
                pageSize: 10,
                type: 'server',
            },
            mockedRuleId,
            mockedAdGroupId,
            mockedStartDate,
            mockedEndDate
        );
        tick();

        expect(store.state.entities).toEqual(mockedHistories);
        expect(rulesServiceStub.listHistories).toHaveBeenCalledTimes(1);
        expect(rulesServiceStub.listHistories).toHaveBeenCalledWith(
            mockedAgencyId,
            mockedAccountId,
            0,
            10,
            mockedRuleId,
            mockedAdGroupId,
            mockedStartDate,
            mockedEndDate,
            (<any>store).requestStateUpdater
        );
    }));
});
