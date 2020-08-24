import {fakeAsync, tick} from '@angular/core/testing';
import {asapScheduler, of, noop} from 'rxjs';
import * as clone from 'clone';
import {CreditsStore} from './credits.store';
import {CreditsService} from '../../../../core/credits/services/credits.service';
import {CreditsStoreFieldsErrorsState} from './credits.store.fields-errors-state';
import {CreditsStoreState} from './credits.store.state';
import {Credit} from '../../../../core/credits/types/credit';
import {CreditRefund} from '../../../../core/credits/types/credit-refund';
import {CreditTotal} from '../../../../core/credits/types/credit-total';
import {CampaignBudget} from '../../../../core/entities/types/campaign/campaign-budget';
import {Account} from '../../../../core/entities/types/account/account';
import {AccountService} from '../../../../core/entities/services/account/account.service';
import * as mockHelpers from '../../../../testing/mock.helpers';
import {ScopeSelectorState} from '../../../../shared/components/scope-selector/scope-selector.constants';
import {PaginationOptions} from '../../../../shared/components/smart-grid/types/pagination-options';
import {CreditStatus, Currency} from '../../../../app.constants';
import {AuthStore} from '../../../../core/auth/services/auth.store';

describe('CreditsLibraryStore', () => {
    let creditsServiceStub: jasmine.SpyObj<CreditsService>;
    let accountsServiceStub: jasmine.SpyObj<AccountService>;
    let authStoreStub: jasmine.SpyObj<AuthStore>;
    let store: CreditsStore;
    let mockedCreditTotals: CreditTotal[];
    let mockedActiveCredits: Credit[];
    let mockedPastCredits: Credit[];
    let mockedCreditRefunds: CreditRefund[];
    let mockedCampaignBudgets: CampaignBudget[];
    let mockedAgencyId: string;
    let mockedAccountId: string;
    let mockedAccounts: Account[];
    let paginationOptions: PaginationOptions;
    const date = new Date();

    beforeEach(() => {
        creditsServiceStub = jasmine.createSpyObj(CreditsService.name, [
            'listActive',
            'listPast',
            'save',
            'totals',
            'listBudgets',
            'listRefunds',
            'createRefund',
        ]);
        accountsServiceStub = jasmine.createSpyObj(AccountService.name, [
            'list',
        ]);
        authStoreStub = jasmine.createSpyObj(AuthStore.name, [
            'hasAgencyScope',
            'hasReadOnlyAccessOn',
        ]);
        store = new CreditsStore(
            creditsServiceStub,
            accountsServiceStub,
            authStoreStub
        );

        mockedAgencyId = '71';
        mockedAccountId = '55';

        mockedCreditTotals = [
            {
                total: '100.00',
                allocated: '100.00',
                past: '0.00',
                available: '0.00',
                currency: Currency.USD,
            },
        ];
        mockedActiveCredits = [
            {
                id: '123',
                accountId: mockedAccountId,
                agencyId: mockedAgencyId,
                total: '300.00',
                startDate: date,
                endDate: new Date(1970, 2, 1),
                licenseFee: '15',
                serviceFee: '15',
                currency: Currency.USD,
                contractId: '4321',
                contractNumber: '1234',
                status: CreditStatus.SIGNED,
                comment: null,
                amount: 50,
            },
            {
                id: '321',
                accountId: mockedAccountId,
                agencyId: mockedAgencyId,
                total: '300.00',
                startDate: date,
                endDate: new Date(1970, 2, 1),
                licenseFee: '15',
                serviceFee: '15',
                currency: Currency.USD,
                contractId: '4321',
                contractNumber: '1234',
                status: CreditStatus.SIGNED,
                comment: null,
                amount: 50,
            },
        ];
        mockedPastCredits = [
            {
                id: '567',
                accountId: mockedAccountId,
                agencyId: mockedAgencyId,
                total: '300.00',
                startDate: date,
                endDate: new Date(1970, 2, 1),
                licenseFee: '15',
                serviceFee: '15',
                currency: Currency.USD,
                contractId: '4321',
                contractNumber: '1234',
                status: CreditStatus.SIGNED,
                comment: null,
                amount: 50,
            },
            {
                id: '765',
                accountId: mockedAccountId,
                agencyId: mockedAgencyId,
                total: '300.00',
                startDate: date,
                endDate: new Date(1970, 2, 1),
                licenseFee: '15',
                serviceFee: '15',
                currency: Currency.USD,
                contractId: '4321',
                contractNumber: '1234',
                status: CreditStatus.SIGNED,
                comment: null,
                amount: 50,
            },
        ];
        mockedCreditRefunds = [
            {
                id: '789',
                creditId: '123',
                accountId: mockedAccountId,
                amount: 100,
                startDate: date,
                effectiveMargin: '0',
                comment: null,
            },
            {
                id: '987',
                creditId: '321',
                accountId: mockedAccountId,
                amount: 100,
                startDate: date,
                effectiveMargin: '0',
                comment: null,
            },
        ];
        mockedCampaignBudgets = [
            {
                id: '456',
                creditId: '123',
                canEditAmount: false,
                canEditEndDate: false,
                canEditStartDate: false,
                comment: null,
                startDate: date,
                endDate: date,
                amount: '20',
                margin: '5',
            },
        ];

        mockedAccounts = [mockHelpers.getMockedAccount()];

        paginationOptions = {
            page: 1,
            pageSize: 20,
            type: 'server',
        };
    });

    it('should correctly initialize store', fakeAsync(() => {
        creditsServiceStub.listActive.and
            .returnValue(of(mockedActiveCredits, asapScheduler))
            .calls.reset();
        creditsServiceStub.listPast.and
            .returnValue(of(mockedPastCredits, asapScheduler))
            .calls.reset();
        creditsServiceStub.totals.and
            .returnValue(of(mockedCreditTotals, asapScheduler))
            .calls.reset();

        accountsServiceStub.list.and
            .returnValue(of(mockedAccounts, asapScheduler))
            .calls.reset();

        store.setStore(
            mockedAgencyId,
            mockedAccountId,
            paginationOptions,
            paginationOptions
        );
        tick();

        expect(store.state.totals).toEqual(mockedCreditTotals);
        expect(store.state.activeCredits).toEqual(mockedActiveCredits);
        expect(store.state.pastCredits).toEqual(mockedPastCredits);
        expect(store.state.agencyId).toEqual(mockedAgencyId);
        expect(store.state.accountId).toEqual(mockedAccountId);
        expect(store.state.accounts).toEqual(mockedAccounts);
        expect(creditsServiceStub.totals).toHaveBeenCalledTimes(1);
        expect(creditsServiceStub.listActive).toHaveBeenCalledTimes(1);
        expect(creditsServiceStub.listPast).toHaveBeenCalledTimes(1);
        expect(accountsServiceStub.list).toHaveBeenCalledTimes(1);
    }));

    it('should list active credits via service', fakeAsync(() => {
        creditsServiceStub.listActive.and
            .returnValue(of(mockedActiveCredits, asapScheduler))
            .calls.reset();

        store.loadEntities(true, paginationOptions);
        tick();

        expect(store.state.activeCredits).toEqual(mockedActiveCredits);
        expect(creditsServiceStub.listActive).toHaveBeenCalledTimes(1);
    }));

    it('should list past credits via service', fakeAsync(() => {
        creditsServiceStub.listPast.and
            .returnValue(of(mockedPastCredits, asapScheduler))
            .calls.reset();

        store.loadEntities(false, paginationOptions);
        tick();

        expect(store.state.pastCredits).toEqual(mockedPastCredits);
        expect(creditsServiceStub.listPast).toHaveBeenCalledTimes(1);
    }));

    it('should change active entity', fakeAsync(() => {
        const mockedCredit = clone(mockedActiveCredits[0]);
        const change = {
            target: mockedCredit,
            changes: {
                id: '987',
            },
        };

        store.changeCreditActiveEntity(change);
        tick();

        expect(store.state.creditActiveEntity.entity.id).toEqual('987');
    }));

    it('should correctly set existing agency credit to creditActiveEntity', () => {
        const mockedCredit = clone(mockedActiveCredits[0]);
        mockedCredit.agencyId = mockedAgencyId;
        mockedCredit.accountId = null;
        store.state.agencyId = mockedAgencyId;
        store.state.hasAgencyScope = true;
        authStoreStub.hasReadOnlyAccessOn.and.returnValue(false).calls.reset();

        const mockedEmptyCredit = new CreditsStoreState().creditActiveEntity
            .entity;
        store.setCreditActiveEntity(mockedCredit);

        expect(store.state.creditActiveEntity.entity).toEqual({
            ...mockedEmptyCredit,
            ...mockedCredit,
        });
        expect(store.state.creditActiveEntity.scopeState).toEqual(
            ScopeSelectorState.AGENCY_SCOPE
        );
        expect(store.state.creditActiveEntity.isReadOnly).toEqual(false);
    });

    it('should correctly set existing agency credit to creditActiveEntity with read only', () => {
        const mockedCredit = clone(mockedActiveCredits[0]);
        mockedCredit.agencyId = mockedAgencyId;
        mockedCredit.accountId = null;
        store.state.agencyId = mockedAgencyId;
        store.state.accountId = mockedAccountId;
        store.state.hasAgencyScope = false;
        authStoreStub.hasReadOnlyAccessOn.and.returnValue(true).calls.reset();

        const mockedEmptyCredit = new CreditsStoreState().creditActiveEntity
            .entity;
        store.setCreditActiveEntity(mockedCredit);

        expect(store.state.creditActiveEntity.entity).toEqual({
            ...mockedEmptyCredit,
            ...mockedCredit,
        });
        expect(store.state.creditActiveEntity.scopeState).toEqual(
            ScopeSelectorState.AGENCY_SCOPE
        );
        expect(store.state.creditActiveEntity.isReadOnly).toEqual(true);
    });

    it('should correctly set existing account credit to creditActiveEntity', () => {
        const mockedCredit = clone(mockedActiveCredits[0]);
        mockedCredit.agencyId = null;
        mockedCredit.accountId = mockedAccountId;
        store.state.agencyId = mockedAgencyId;
        store.state.accountId = mockedAccountId;
        store.state.hasAgencyScope = false;
        authStoreStub.hasReadOnlyAccessOn.and.returnValue(false).calls.reset();

        const mockedEmptyCredit = new CreditsStoreState().creditActiveEntity
            .entity;
        store.setCreditActiveEntity(mockedCredit);

        expect(store.state.creditActiveEntity.entity).toEqual({
            ...mockedEmptyCredit,
            ...mockedCredit,
        });
        expect(store.state.creditActiveEntity.scopeState).toEqual(
            ScopeSelectorState.ACCOUNT_SCOPE
        );
        expect(store.state.creditActiveEntity.isReadOnly).toEqual(false);
    });

    it('should correctly set new account credit to creditActiveEntity', () => {
        store.state.agencyId = mockedAgencyId;
        store.state.accountId = mockedAccountId;
        store.state.hasAgencyScope = true;

        store.setCreditActiveEntity({});

        expect(store.state.creditActiveEntity.entity).toEqual({
            ...new CreditsStoreState().creditActiveEntity.entity,
            accountId: mockedAccountId,
        });
        expect(store.state.creditActiveEntity.scopeState).toEqual(
            ScopeSelectorState.ACCOUNT_SCOPE
        );
    });

    it('should correctly set new agency credit to creditActiveEntity', () => {
        store.state.agencyId = mockedAgencyId;
        store.state.accountId = null;
        store.state.hasAgencyScope = true;

        store.setCreditActiveEntity({});

        expect(store.state.creditActiveEntity.entity).toEqual({
            ...new CreditsStoreState().creditActiveEntity.entity,
            agencyId: mockedAgencyId,
        });
        expect(store.state.creditActiveEntity.scopeState).toEqual(
            ScopeSelectorState.AGENCY_SCOPE
        );
    });

    it('should set account to creditActiveEntity', () => {
        store.state.creditActiveEntity.entity = clone(mockedActiveCredits[0]);

        store.setCreditActiveEntityAccount(mockedAccountId);

        expect(store.state.creditActiveEntity.entity.accountId).toEqual(
            mockedAccountId
        );
    });

    it('should set creditActiveEntity scope to account scope', () => {
        store.state.accounts = clone(mockedAccounts);
        store.state.creditActiveEntity.entity = clone(mockedActiveCredits[0]);
        store.state.creditActiveEntity.scopeState =
            ScopeSelectorState.AGENCY_SCOPE;
        store.state.accountId = mockedAccountId;

        store.setCreditActiveEntityScope(ScopeSelectorState.ACCOUNT_SCOPE);

        expect(store.state.creditActiveEntity.entity.accountId).toEqual(
            mockedAccountId
        );
        expect(store.state.creditActiveEntity.entity.agencyId).toEqual(null);
        expect(store.state.creditActiveEntity.scopeState).toEqual(
            ScopeSelectorState.ACCOUNT_SCOPE
        );
    });

    it('should set creditActiveEntity scope to agency scope', () => {
        store.state.creditActiveEntity.entity = clone(mockedActiveCredits[0]);
        store.state.creditActiveEntity.entity.agencyId = null;
        store.state.creditActiveEntity.entity.accountId = mockedAccountId;
        store.state.creditActiveEntity.scopeState =
            ScopeSelectorState.ACCOUNT_SCOPE;
        store.state.agencyId = mockedAgencyId;

        store.setCreditActiveEntityScope(ScopeSelectorState.AGENCY_SCOPE);

        expect(store.state.creditActiveEntity.entity.agencyId).toEqual(
            mockedAgencyId
        );
        expect(store.state.creditActiveEntity.entity.accountId).toEqual(null);
        expect(store.state.creditActiveEntity.scopeState).toEqual(
            ScopeSelectorState.AGENCY_SCOPE
        );
    });

    it('should load campaign budgets', fakeAsync(() => {
        const mockedCredit = clone(mockedActiveCredits[0]);
        store.setCreditActiveEntity(mockedCredit);

        creditsServiceStub.listBudgets.and
            .returnValue(of(mockedCampaignBudgets, asapScheduler))
            .calls.reset();

        store.loadCreditActiveEntityBudgets();
        tick();

        expect(store.state.creditActiveEntity.campaignBudgets).toEqual(
            mockedCampaignBudgets
        );
        expect(creditsServiceStub.listBudgets).toHaveBeenCalledTimes(1);
    }));

    it('should save credit item', fakeAsync(() => {
        const mockedCredit = clone(mockedActiveCredits[0]);
        const mockedEmptyCredit = new CreditsStoreState().creditActiveEntity
            .entity;
        store.setCreditActiveEntity(mockedCredit);

        creditsServiceStub.save.and
            .returnValue(of(mockedCredit, asapScheduler))
            .calls.reset();

        store.saveCreditActiveEntity();
        tick();

        expect(store.state.creditActiveEntity.entity).toEqual(
            mockedEmptyCredit
        );
        expect(creditsServiceStub.save).toHaveBeenCalledTimes(1);
    }));

    it('should cancel credit item', fakeAsync(() => {
        const mockedCredit = clone(mockedActiveCredits[0]);
        const mockedEmptyCredit = new CreditsStoreState().creditActiveEntity
            .entity;
        store.setCreditActiveEntity(mockedCredit);

        creditsServiceStub.save.and
            .returnValue(of(mockedCredit, asapScheduler))
            .calls.reset();

        store.cancelCreditActiveEntity();
        tick();

        expect(store.state.creditActiveEntity.entity).toEqual(
            mockedEmptyCredit
        );
        expect(creditsServiceStub.save).toHaveBeenCalledTimes(1);
    }));

    it('should not cancel credit item with no id', fakeAsync(() => {
        const mockedCredit = clone(mockedActiveCredits[0]);
        mockedCredit.id = null;
        store.setCreditActiveEntity(mockedCredit);

        creditsServiceStub.save.and
            .returnValue(of(mockedCredit, asapScheduler))
            .calls.reset();

        store.cancelCreditActiveEntity();
        tick();
        expect(creditsServiceStub.save).toHaveBeenCalledTimes(0);
    }));

    it('should load refunds', fakeAsync(() => {
        const creditId = '123';

        creditsServiceStub.listRefunds.and
            .returnValue(of(mockedCreditRefunds, asapScheduler))
            .calls.reset();

        store.loadRefunds(creditId, paginationOptions);
        tick();

        expect(store.state.creditRefunds).toEqual(mockedCreditRefunds);
        expect(creditsServiceStub.listRefunds).toHaveBeenCalledTimes(1);
    }));

    it('should create refund', fakeAsync(() => {
        const mockedCredit = clone(mockedActiveCredits[0]);
        const mockedCreditRefund = clone(mockedCreditRefunds[0]);
        const mockedEmptyCreditRefund = new CreditsStoreState()
            .creditRefundActiveEntity.entity;

        store.setCreditActiveEntity(mockedCredit);
        store.setCreditRefundActiveEntity(mockedCreditRefund);

        creditsServiceStub.createRefund.and
            .returnValue(of(mockedCreditRefund, asapScheduler))
            .calls.reset();

        store.saveCreditRefundActiveEntity();
        tick();

        expect(store.state.creditRefundActiveEntity.entity).toEqual(
            mockedEmptyCreditRefund
        );
        expect(creditsServiceStub.createRefund).toHaveBeenCalledTimes(1);
    }));
});
