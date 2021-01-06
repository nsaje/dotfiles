import {fakeAsync, tick} from '@angular/core/testing';
import {asapScheduler, of} from 'rxjs';
import {RulesService} from '../../../../core/rules/services/rules.service';
import {RulesHistoriesStore} from './rules-histories.store';
import {RuleHistory} from '../../../../core/rules/types/rule-history';
import {
    RuleHistoryStatus,
    RuleTargetType,
    RuleActionType,
    RuleActionFrequency,
    TimeRange,
    RuleNotificationType,
} from '../../../../core/rules/rules.constants';
import {AdGroupService} from '../../../../core/entities/services/ad-group/ad-group.service';
import {Rule} from '../../../../core/rules/types/rule';
import {AdGroup} from '../../../../core/entities/types/ad-group/ad-group';
import {
    BiddingType,
    AdGroupState,
    DeliveryType,
} from '../../../../app.constants';

describe('RulesHistoriesStore', () => {
    let rulesServiceStub: jasmine.SpyObj<RulesService>;
    let adGroupServiceStub: jasmine.SpyObj<AdGroupService>;
    let store: RulesHistoriesStore;
    let mockedHistories: RuleHistory[];
    let mockedRules: Rule[];
    let mockedAdGroups: AdGroup[];
    let mockedAgencyId: string;
    let mockedAccountId: string;
    let mockedRuleId: string;
    let mockedAdGroupId: string;
    let mockedStartDate: Date;
    let mockedEndDate: Date;
    let mockedKeyword: string;

    beforeEach(() => {
        rulesServiceStub = jasmine.createSpyObj(RulesService.name, [
            'list',
            'get',
            'listHistories',
        ]);
        adGroupServiceStub = jasmine.createSpyObj(AdGroupService.name, [
            'get',
            'list',
        ]);

        store = new RulesHistoriesStore(rulesServiceStub, adGroupServiceStub);

        const date = new Date();

        mockedHistories = [
            {
                id: '10000000',
                createdDt: date,
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
                publisherGroup: null,
                window: TimeRange.LastSixtyDays,
                notificationType: RuleNotificationType.OnRuleRun,
                notificationRecipients: ['test@test.com'],
                conditions: [],
            },
        ];

        mockedAdGroups = [
            {
                id: '10000000',
                campaignId: '10000000',
                name: 'Test Ad Group',
                biddingType: BiddingType.CPC,
                state: AdGroupState.ACTIVE,
                archived: false,
                startDate: date,
                endDate: date,
                trackingCode: '',
                bid: '',
                deliveryType: DeliveryType.STANDARD,
                clickCappingDailyAdGroupMaxClicks: 1,
                dayparting: {},
                deals: [],
                targeting: {},
                autopilot: null,
                manageRtbSourcesAsOne: false,
                frequencyCapping: 1,
                notes: '',
                dailyBudget: '50',
            },
        ];

        mockedAgencyId = '71';
        mockedAccountId = '55';
        mockedRuleId = '10000000';
        mockedAdGroupId = '1234';
        mockedStartDate = date;
        mockedEndDate = date;
        mockedKeyword = 'keyword';
    });

    it('should correctly initialize store', fakeAsync(() => {
        rulesServiceStub.listHistories.and
            .returnValue(of(mockedHistories, asapScheduler))
            .calls.reset();
        rulesServiceStub.get.and
            .returnValue(of(mockedRules[0], asapScheduler))
            .calls.reset();
        adGroupServiceStub.get.and
            .returnValue(
                of(
                    {adGroup: mockedAdGroups[0], extras: {} as any},
                    asapScheduler
                )
            )
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
            mockedEndDate,
            true
        );
        tick();

        expect(store.state.entities).toEqual(mockedHistories);
        expect(store.state.rules).toEqual([mockedRules[0]]);
        expect(store.state.adGroups).toEqual([mockedAdGroups[0]]);
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
            true,
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
            mockedEndDate,
            true
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
            true,
            (<any>store).requestStateUpdater
        );
    }));

    it('should list rules via service', fakeAsync(() => {
        store.state.agencyId = mockedAgencyId;
        store.state.accountId = mockedAccountId;

        rulesServiceStub.list.and
            .returnValue(of(mockedRules, asapScheduler))
            .calls.reset();
        store.searchRules(mockedKeyword);
        tick();

        expect(store.state.rules).toEqual(mockedRules);
        expect(rulesServiceStub.list).toHaveBeenCalledTimes(1);
        expect(rulesServiceStub.list).toHaveBeenCalledWith(
            mockedAgencyId,
            mockedAccountId,
            0,
            20,
            mockedKeyword,
            false,
            (<any>store).requestStateUpdater
        );
    }));

    it('should list ad groups via service', fakeAsync(() => {
        store.state.agencyId = mockedAgencyId;
        store.state.accountId = mockedAccountId;

        adGroupServiceStub.list.and
            .returnValue(of(mockedAdGroups, asapScheduler))
            .calls.reset();
        store.searchAdGroups(mockedKeyword);
        tick();

        expect(store.state.adGroups).toEqual(mockedAdGroups);
        expect(adGroupServiceStub.list).toHaveBeenCalledTimes(1);
        expect(adGroupServiceStub.list).toHaveBeenCalledWith(
            mockedAgencyId,
            mockedAccountId,
            0,
            20,
            mockedKeyword,
            (<any>store).adGroupRequestStateUpdater
        );
    }));
});
