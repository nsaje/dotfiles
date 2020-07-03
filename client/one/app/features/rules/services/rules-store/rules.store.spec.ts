import {fakeAsync, tick} from '@angular/core/testing';
import {asapScheduler, of, noop} from 'rxjs';
import {AccountService} from '../../../../core/entities/services/account/account.service';
import {Account} from '../../../../core/entities/types/account/account';
import * as mockHelpers from '../../../../testing/mock.helpers';
import {RulesService} from '../../../../core/rules/services/rules.service';
import {RulesStore} from './rules.store';
import {Rule} from '../../../../core/rules/types/rule';
import {
    RuleTargetType,
    RuleActionType,
    RuleActionFrequency,
    RuleNotificationType,
    TimeRange,
} from '../../../../core/rules/rules.constants';

describe('RulesLibraryStore', () => {
    let rulesServiceStub: jasmine.SpyObj<RulesService>;
    let accountsServiceStub: jasmine.SpyObj<AccountService>;
    let zemPermissionsStub: any;
    let store: RulesStore;
    let mockedRules: Rule[];
    let mockedAgencyId: string;
    let mockedAccountId: string;
    let mockedAccounts: Account[];

    beforeEach(() => {
        rulesServiceStub = jasmine.createSpyObj(RulesService.name, ['list']);
        accountsServiceStub = jasmine.createSpyObj(AccountService.name, [
            'list',
        ]);
        zemPermissionsStub = jasmine.createSpyObj('zemPermissions', [
            'hasAgencyScope',
        ]);
        store = new RulesStore(
            rulesServiceStub,
            accountsServiceStub,
            zemPermissionsStub
        );
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

        mockedAgencyId = '71';
        mockedAccountId = '55';

        mockedAccounts = [mockHelpers.getMockedAccount()];
    });

    it('should correctly initialize store', fakeAsync(() => {
        const mockedPage = 1;
        const mockedPageSize = 10;
        rulesServiceStub.list.and
            .returnValue(of(mockedRules, asapScheduler))
            .calls.reset();
        accountsServiceStub.list.and
            .returnValue(of(mockedAccounts, asapScheduler))
            .calls.reset();
        store.setStore(
            mockedAgencyId,
            mockedAccountId,
            mockedPage,
            mockedPageSize
        );
        tick();

        expect(store.state.entities).toEqual(mockedRules);
        expect(store.state.accountId).toEqual(mockedAccountId);
        expect(store.state.accounts).toEqual(mockedAccounts);
        expect(rulesServiceStub.list).toHaveBeenCalledTimes(1);
        expect(accountsServiceStub.list).toHaveBeenCalledTimes(1);
        expect(rulesServiceStub.list).toHaveBeenCalledWith(
            mockedAgencyId,
            mockedAccountId,
            0,
            10,
            null,
            (<any>store).requestStateUpdater
        );
    }));

    it('should list rules via service', fakeAsync(() => {
        const mockedPage = 1;
        const mockedPageSize = 10;
        store.state.agencyId = mockedAgencyId;

        rulesServiceStub.list.and
            .returnValue(of(mockedRules, asapScheduler))
            .calls.reset();
        store.loadEntities(mockedPage, mockedPageSize);
        tick();

        expect(store.state.entities).toEqual(mockedRules);
        expect(rulesServiceStub.list).toHaveBeenCalledTimes(1);
        expect(rulesServiceStub.list).toHaveBeenCalledWith(
            mockedAgencyId,
            null,
            0,
            10,
            null,
            (<any>store).requestStateUpdater
        );
    }));
});
