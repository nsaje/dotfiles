import {fakeAsync, tick} from '@angular/core/testing';
import {asapScheduler, of} from 'rxjs';
import {AgencyService} from '../../../core/entities/services/agency/agency.service';
import {AccountService} from '../../../core/entities/services/account/account.service';
import {SidebarContentStore} from './sidebar-content.store';
import {Agency} from '../../../core/entities/types/agency/agency';
import {Account} from '../../../core/entities/types/account/account';
import * as mockHelpers from '../../../testing/mock.helpers';

describe('SidebarContentStore', () => {
    let agencyServiceStub: jasmine.SpyObj<AgencyService>;
    let accountServiceStub: jasmine.SpyObj<AccountService>;
    let zemPermissionsStub: any;
    let store: SidebarContentStore;
    let mockedAgencies: Agency[];
    let mockedAccounts: Account[];
    let mockedAccount: Account;
    let mockedAgencyId: string;
    let mockedAccountId: string;

    beforeEach(() => {
        agencyServiceStub = jasmine.createSpyObj(AgencyService.name, ['list']);
        accountServiceStub = jasmine.createSpyObj(AccountService.name, [
            'list',
        ]);
        zemPermissionsStub = jasmine.createSpyObj('zemPermissions', [
            'hasAgencyScope',
        ]);
        store = new SidebarContentStore(
            agencyServiceStub,
            accountServiceStub,
            zemPermissionsStub
        );
        mockedAgencies = [
            {
                id: '1',
                name: 'mocked agency 1',
            },
            {
                id: '2',
                name: 'mocked agency 2',
            },
            {
                id: '3',
                name: 'mocked agency 3',
            },
        ];
        mockedAccount = mockHelpers.getMockedAccount();
        mockedAccounts = [
            {...mockedAccount, id: '1'},
            {...mockedAccount, id: '2'},
            {...mockedAccount, id: '3'},
        ];

        mockedAgencyId = '25';
        mockedAccountId = '34';
    });

    it('should correctly initialize store with agency and account', fakeAsync(() => {
        agencyServiceStub.list.and
            .returnValue(of(mockedAgencies, asapScheduler))
            .calls.reset();
        accountServiceStub.list.and
            .returnValue(of(mockedAccounts, asapScheduler))
            .calls.reset();
        zemPermissionsStub.hasAgencyScope.and.returnValue(true).calls.reset();
        store.init('1', '2');
        tick();

        expect(store.state.agencies).toEqual(mockedAgencies);
        expect(store.state.accounts).toEqual(mockedAccounts);
        expect(store.state.selectedAgencyId).toEqual('1');
        expect(store.state.selectedAccountId).toEqual('2');
        expect(agencyServiceStub.list).toHaveBeenCalledTimes(1);
        expect(accountServiceStub.list).toHaveBeenCalledTimes(1);
        expect(zemPermissionsStub.hasAgencyScope).toHaveBeenCalledTimes(0);
    }));

    it('should correctly initialize store with only agency and agency user scope', fakeAsync(() => {
        agencyServiceStub.list.and
            .returnValue(of(mockedAgencies, asapScheduler))
            .calls.reset();
        accountServiceStub.list.and
            .returnValue(of(mockedAccounts, asapScheduler))
            .calls.reset();
        zemPermissionsStub.hasAgencyScope.and.returnValue(true).calls.reset();
        store.init('1', null);
        tick();

        expect(store.state.agencies).toEqual(mockedAgencies);
        expect(store.state.accounts).toEqual(mockedAccounts);
        expect(store.state.selectedAgencyId).toEqual('1');
        expect(store.state.selectedAccountId).toEqual(null);
        expect(agencyServiceStub.list).toHaveBeenCalledTimes(1);
        expect(accountServiceStub.list).toHaveBeenCalledTimes(1);
        expect(zemPermissionsStub.hasAgencyScope).toHaveBeenCalledTimes(1);
    }));

    it('should correctly initialize store with only agency and account user scope', fakeAsync(() => {
        agencyServiceStub.list.and
            .returnValue(of(mockedAgencies, asapScheduler))
            .calls.reset();
        accountServiceStub.list.and
            .returnValue(of(mockedAccounts, asapScheduler))
            .calls.reset();
        zemPermissionsStub.hasAgencyScope.and.returnValue(false).calls.reset();
        store.init('1', null);
        tick();

        expect(store.state.agencies).toEqual(mockedAgencies);
        expect(store.state.accounts).toEqual(mockedAccounts);
        expect(store.state.selectedAgencyId).toEqual('1');
        expect(store.state.selectedAccountId).toEqual(mockedAccounts[0].id);
        expect(agencyServiceStub.list).toHaveBeenCalledTimes(1);
        expect(accountServiceStub.list).toHaveBeenCalledTimes(1);
        expect(zemPermissionsStub.hasAgencyScope).toHaveBeenCalledTimes(1);
    }));

    it('should correctly set selected agency id with agency scope', fakeAsync(() => {
        store.state.selectedAgencyId = mockedAgencyId;
        store.state.selectedAccountId = mockedAccountId;
        accountServiceStub.list.and
            .returnValue(of(mockedAccounts, asapScheduler))
            .calls.reset();
        zemPermissionsStub.hasAgencyScope.and.returnValue(true).calls.reset();
        store.setSelectedAgency('2');
        tick();

        expect(store.state.selectedAgencyId).toEqual('2');
        expect(store.state.selectedAccountId).toEqual(null);
        expect(store.state.selectedAccountId).not.toEqual(mockedAccountId);
        expect(accountServiceStub.list).toHaveBeenCalledTimes(1);
    }));

    it('should correctly set selected agency id with account scope', fakeAsync(() => {
        store.state.selectedAgencyId = mockedAgencyId;
        store.state.selectedAccountId = mockedAccountId;
        accountServiceStub.list.and
            .returnValue(of(mockedAccounts, asapScheduler))
            .calls.reset();
        zemPermissionsStub.hasAgencyScope.and.returnValue(false).calls.reset();
        store.setSelectedAgency('2');
        tick();

        expect(store.state.selectedAgencyId).toEqual('2');
        expect(store.state.selectedAccountId).toEqual(mockedAccounts[0].id);
        expect(store.state.selectedAccountId).not.toEqual(mockedAccountId);
        expect(accountServiceStub.list).toHaveBeenCalledTimes(1);
    }));

    it('should correctly set selected account id', fakeAsync(() => {
        store.state.selectedAccountId = mockedAccountId;
        store.setSelectedAccount('1');
        tick();

        expect(store.state.selectedAccountId).toEqual('1');
    }));
});
