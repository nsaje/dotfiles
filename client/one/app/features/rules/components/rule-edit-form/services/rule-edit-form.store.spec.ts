import {fakeAsync, tick} from '@angular/core/testing';
import {asapScheduler, of} from 'rxjs';
import * as clone from 'clone';
import {RuleEditFormStore} from './rule-edit-form.store';
import {RulesService} from '../../../../../core/rules/services/rules.service';
import {PublisherGroupsService} from '../../../../../core/publisher-groups/services/publisher-groups.service';
import {Rule} from '../../../../../core/rules/types/rule';
import {
    TimeRange,
    RuleNotificationType,
} from '../../../../../core/rules/rules.constants';
import {PublisherGroup} from '../../../../../core/publisher-groups/types/publisher-group';
import {AccountService} from '../../../../../core/entities/services/account/account.service';
import {Account} from '../../../../../core/entities/types/account/account';
import * as mockHelpers from '../../../../../testing/mock.helpers';
import {AdGroupService} from '../../../../../core/entities/services/ad-group/ad-group.service';
import {CampaignService} from '../../../../../core/entities/services/campaign/campaign.service';
import {EntityType} from '../../../../../app.constants';

describe('RuleEditFormStore', () => {
    let rulesServiceStub: jasmine.SpyObj<RulesService>;
    let publisherGroupsServiceStub: jasmine.SpyObj<PublisherGroupsService>;
    let accountsServiceStub: jasmine.SpyObj<AccountService>;
    let campaignServiceStub: jasmine.SpyObj<CampaignService>;
    let adGroupServiceStub: jasmine.SpyObj<AdGroupService>;
    let zemPermissionsStub: any;

    let store: RuleEditFormStore;
    let mockedAgencyId: string;
    let mockedAccountId: string;
    let mockedAdGroupId: string;
    let mockedAdGroupName: string;
    let mockedRule: Rule;
    let mockedPublisherGroups: PublisherGroup[];
    let mockedAccounts: Account[];

    beforeEach(() => {
        rulesServiceStub = jasmine.createSpyObj(RulesService.name, ['save']);
        publisherGroupsServiceStub = jasmine.createSpyObj(
            PublisherGroupsService.name,
            ['listImplicit', 'listExplicit']
        );
        accountsServiceStub = jasmine.createSpyObj(AccountService.name, [
            'list',
        ]);
        campaignServiceStub = jasmine.createSpyObj(CampaignService.name, [
            'list',
        ]);
        adGroupServiceStub = jasmine.createSpyObj(AdGroupService.name, [
            'list',
        ]);
        zemPermissionsStub = jasmine.createSpyObj('zemPermissions', [
            'hasAgencyScope',
        ]);
        store = new RuleEditFormStore(
            rulesServiceStub,
            publisherGroupsServiceStub,
            accountsServiceStub,
            campaignServiceStub,
            adGroupServiceStub,
            zemPermissionsStub
        );

        mockedAgencyId = '123';
        mockedAccountId = '12';
        mockedAdGroupId = '12345';
        mockedAdGroupName = 'Ad Group 12345';
        mockedRule = {
            id: null,
            agencyId: mockedAgencyId,
            accountId: null,
            name: null,
            entities: {},
            targetType: null,
            actionType: null,
            actionFrequency: null,
            changeStep: null,
            changeLimit: null,
            sendEmailRecipients: [],
            sendEmailSubject: null,
            sendEmailBody: null,
            publisherGroupId: null,
            conditions: [],
            window: TimeRange.Lifetime,
            notificationType: RuleNotificationType.None,
            notificationRecipients: [],
        };

        mockedPublisherGroups = [
            {
                id: '10000000',
                name: 'Test publisher group',
                agencyId: mockedAgencyId,
                accountId: null,
                includeSubdomains: null,
                size: null,
                implicit: null,
                modifiedDt: null,
                createdDt: null,
                type: null,
                level: null,
                levelName: null,
                levelId: null,
                entries: null,
            },
        ];

        mockedAccounts = [mockHelpers.getMockedAccount()];
    });

    it('should correctly initialize store', fakeAsync(() => {
        accountsServiceStub.list.and
            .returnValue(of(mockedAccounts, asapScheduler))
            .calls.reset();

        store.initStore(
            mockedAgencyId,
            mockedAccountId,
            {},
            mockedAdGroupId,
            mockedAdGroupName,
            EntityType.AD_GROUP
        );
        tick();

        const mockedNewRule = clone(mockedRule);
        mockedNewRule.entities = {
            accounts: {
                included: [],
            },
            campaigns: {
                included: [],
            },
            adGroups: {
                included: [{id: mockedAdGroupId, name: mockedAdGroupName}],
            },
        };

        expect(store.state.agencyId).toEqual(mockedAgencyId);
        expect(store.state.accountId).toEqual(mockedAccountId);
        expect(store.state.rule.entities).toEqual(mockedNewRule.entities);
        expect(store.state.availableConditions).toEqual([]);
        expect(store.state.fieldsErrors).toEqual(null);
        expect(store.state.requests).toEqual({save: {}});
        expect(store.state.accounts).toEqual(mockedAccounts);
        expect(accountsServiceStub.list).toHaveBeenCalledTimes(1);
    }));

    it('should correctly split notification recipients', fakeAsync(() => {
        accountsServiceStub.list.and
            .returnValue(of(mockedAccounts, asapScheduler))
            .calls.reset();

        store.initStore(
            mockedAgencyId,
            mockedAccountId,
            {},
            mockedAdGroupId,
            mockedAdGroupName,
            EntityType.AD_GROUP
        );

        store.setRuleNotificationRecipients('user@test.com');
        expect(store.state.rule.notificationRecipients).toEqual([
            'user@test.com',
        ]);

        store.setRuleNotificationRecipients('user@test.com,user2@test.com');
        expect(store.state.rule.notificationRecipients).toEqual([
            'user@test.com',
            'user2@test.com',
        ]);

        store.setRuleNotificationRecipients('user@test.com,user2@test.com');
        expect(store.state.rule.notificationRecipients).toEqual([
            'user@test.com',
            'user2@test.com',
        ]);

        store.setRuleNotificationRecipients('user@test.com	user2@test.com');
        expect(store.state.rule.notificationRecipients).toEqual([
            'user@test.com',
            'user2@test.com',
        ]);
    }));

    it('should correctly split send email recipients', fakeAsync(() => {
        accountsServiceStub.list.and
            .returnValue(of(mockedAccounts, asapScheduler))
            .calls.reset();

        store.initStore(
            mockedAgencyId,
            mockedAccountId,
            {},
            mockedAdGroupId,
            mockedAdGroupName,
            EntityType.AD_GROUP
        );

        store.setSendEmailRecipients('user@test.com');
        expect(store.state.rule.sendEmailRecipients).toEqual(['user@test.com']);

        store.setSendEmailRecipients('user@test.com,user2@test.com');
        expect(store.state.rule.sendEmailRecipients).toEqual([
            'user@test.com',
            'user2@test.com',
        ]);

        store.setSendEmailRecipients('user@test.com,user2@test.com');
        expect(store.state.rule.sendEmailRecipients).toEqual([
            'user@test.com',
            'user2@test.com',
        ]);

        store.setSendEmailRecipients('user@test.com	user2@test.com');
        expect(store.state.rule.sendEmailRecipients).toEqual([
            'user@test.com',
            'user2@test.com',
        ]);
    }));

    it('should list publisher groups via publisher group service', fakeAsync(() => {
        const keyword = 'blue';
        publisherGroupsServiceStub.listExplicit.and
            .returnValue(of(mockedPublisherGroups, asapScheduler))
            .calls.reset();
        store.loadAvailablePublisherGroups(keyword);
        tick();

        expect(store.state.availablePublisherGroups).toEqual(
            mockedPublisherGroups
        );
        expect(publisherGroupsServiceStub.listExplicit).toHaveBeenCalledTimes(
            1
        );
    }));
});
