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
import {PublisherGroup} from '../../../../..//core/publisher-groups/types/publisher-group';

describe('RulesLibraryStore', () => {
    let rulesServiceStub: jasmine.SpyObj<RulesService>;
    let publisherGroupsServiceStub: jasmine.SpyObj<PublisherGroupsService>;

    let store: RuleEditFormStore;
    let mockedAgencyId: string;
    let mockedAdGroupId: string;
    let mockedRule: Rule;
    let mockedPublisherGroups: PublisherGroup[];

    beforeEach(() => {
        rulesServiceStub = jasmine.createSpyObj(RulesService.name, ['save']);
        publisherGroupsServiceStub = jasmine.createSpyObj(
            PublisherGroupsService.name,
            ['listImplicit', 'listExplicit']
        );

        store = new RuleEditFormStore(
            rulesServiceStub,
            publisherGroupsServiceStub
        );

        mockedAgencyId = '123';
        mockedAdGroupId = '12345';
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
        expect(store.state.availableConditions).toEqual([]);
        expect(store.state.fieldsErrors).toEqual(null);
        expect(store.state.requests).toEqual({save: {}});
    }));

    it('should correctly split notification recipients', fakeAsync(() => {
        store.initStore(mockedAgencyId, mockedAdGroupId);

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
        store.initStore(mockedAgencyId, mockedAdGroupId);

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
