var of = require('rxjs').of;
var Currency = require('../../../../app.constants').Currency;
var CreditStatus = require('../../../../app.constants').CreditStatus;
var ScopeSelectorState = require('../../../../shared/components/scope-selector/scope-selector.constants')
    .ScopeSelectorState;

describe('zemCreditsStateService', function() {
    var zemCreditsStateService;
    var zemAccountService;
    var zemCreditsEndpoint;
    var zemCreditsRefundEndpoint;
    var zemUserService;
    var zemPermissions;
    var $q;
    var $scope;

    var mockedUser;
    var mockedAgency;
    var mockedAccount;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemPermissions'));
    beforeEach(inject(function(
        _zemCreditsStateService_,
        _zemAccountService_,
        _zemCreditsEndpoint_,
        _zemCreditsRefundEndpoint_,
        _zemUserService_,
        _zemPermissions_,
        _$q_,
        $rootScope
    ) {
        zemCreditsStateService = _zemCreditsStateService_;
        zemAccountService = _zemAccountService_;
        zemCreditsEndpoint = _zemCreditsEndpoint_;
        zemCreditsRefundEndpoint = _zemCreditsRefundEndpoint_;
        zemUserService = _zemUserService_;
        zemPermissions = _zemPermissions_;
        $q = _$q_;
        $scope = $rootScope.$new();

        mockedAgency = {
            id: '123',
            name: 'Test Agency',
        };

        mockedAccount = {
            id: '456',
            name: 'Test Account',
            currency: Currency.USD,
        };

        mockedUser = {
            id: 123,
            permissions: {},
            email: 'internal.user@zemanta.com',
            agencies: [Number(mockedAgency.id)],
        };

        spyOn(zemUserService, 'current').and.callFake(function() {
            return mockedUser;
        });
        spyOn(zemAccountService, 'list').and.callFake(function() {
            return of([mockedAccount]);
        });
        spyOn(zemPermissions, 'hasAgencyScope').and.callFake(function() {
            return true;
        });
    }));

    it('should create instance correctly with agencyId and accountId', function() {
        var agencyId = mockedAgency.id;
        var accountId = mockedAccount.id;

        var stateService = zemCreditsStateService.createInstance(
            agencyId,
            accountId
        );
        var state = stateService.getState();

        expect(state.agencyId).toEqual(agencyId);
        expect(state.accountId).toEqual(accountId);
        expect(state.hasAgencyScope).toEqual(true);
        expect(state.accounts).toEqual([mockedAccount]);
        expect(state.requests.reloadAccounts.inProgress).toEqual(false);
    });

    it('should correctly reload state', function() {
        var agencyId = mockedAgency.id;
        var accountId = mockedAccount.id;

        var mockedTotals = [
            {
                total: '100.00',
                allocated: '100.00',
                past: '0.00',
                available: '0.00',
                currency: Currency.USD,
            },
        ];

        var mockedActiveCredits = [
            {
                id: '123',
                accountId: mockedAccount.id,
                total: '300.00',
            },
            {
                id: '456',
                accountId: mockedAccount.id,
                total: '100.00',
            },
        ];

        var mockedCreditRefunds = [
            {
                id: '123',
                creditId: '123',
                amount: '100.00',
            },
            {
                id: '345',
                creditId: '123',
                amount: '200.00',
            },
            {
                id: '678',
                creditId: '456',
                amount: '100.00',
            },
            {
                id: '910',
                creditId: '456',
                amount: '100.00',
            },
        ];

        spyOn(zemCreditsEndpoint, 'totals').and.callFake(function() {
            return $q.resolve(mockedTotals);
        });
        spyOn(zemCreditsEndpoint, 'listActive').and.callFake(function() {
            return $q.resolve(mockedActiveCredits);
        });
        spyOn(zemCreditsEndpoint, 'listPast').and.callFake(function() {
            return $q.resolve([]);
        });
        spyOn(zemCreditsRefundEndpoint, 'listAll').and.callFake(function() {
            return $q.resolve(mockedCreditRefunds);
        });

        var stateService = zemCreditsStateService.createInstance(
            agencyId,
            accountId
        );
        var state = stateService.getState();

        expect(state.agencyId).toEqual(agencyId);
        expect(state.accountId).toEqual(accountId);
        expect(state.hasAgencyScope).toEqual(true);
        expect(state.accounts).toEqual([mockedAccount]);
        expect(state.requests.reloadAccounts.inProgress).toEqual(false);

        stateService.reload();
        $scope.$digest();
        state = stateService.getState();

        expect(state.totals).toEqual(mockedTotals);
        expect(state.requests.reloadTotals.inProgress).toEqual(false);

        expect(state.credits).toEqual([
            {
                id: '123',
                accountId: mockedAccount.id,
                total: '300.00',
                isReadOnly: false,
            },
            {
                id: '456',
                accountId: mockedAccount.id,
                total: '100.00',
                isReadOnly: false,
            },
        ]);
        expect(state.requests.reloadCredits.inProgress).toEqual(false);

        expect(state.pastCredits).toEqual([]);
        expect(state.requests.reloadPastCredits.inProgress).toEqual(false);

        expect(state.creditRefunds).toEqual({
            '123': [
                {
                    id: '123',
                    creditId: '123',
                    amount: '100.00',
                },
                {
                    id: '345',
                    creditId: '123',
                    amount: '200.00',
                },
            ],
            '456': [
                {
                    id: '678',
                    creditId: '456',
                    amount: '100.00',
                },
                {
                    id: '910',
                    creditId: '456',
                    amount: '100.00',
                },
            ],
        });
        expect(state.creditRefundTotals).toEqual({
            '123': 600,
            '456': 300,
        });
        expect(state.requests.reloadCreditRefunds.inProgress).toEqual(false);
    });

    it('should correctly set new credit item', function() {
        var agencyId = mockedAgency.id;
        var accountId = mockedAccount.id;

        var stateService = zemCreditsStateService.createInstance(
            agencyId,
            accountId
        );
        var state = stateService.getState();

        expect(state.agencyId).toEqual(agencyId);
        expect(state.accountId).toEqual(accountId);
        expect(state.hasAgencyScope).toEqual(true);
        expect(state.accounts).toEqual([mockedAccount]);
        expect(state.requests.reloadAccounts.inProgress).toEqual(false);

        stateService.setCreditItem({});
        state = stateService.getState();

        expect(state.creditItem.status).toEqual(CreditStatus.PENDING);
        expect(state.creditItemScopeState).toEqual(
            ScopeSelectorState.ACCOUNT_SCOPE
        );
        expect(state.creditItem.agencyId).toEqual(undefined);
        expect(state.creditItem.accountId).toEqual(accountId);
        expect(state.creditItem.isReadOnly).toEqual(undefined);
    });

    it('should correctly set existing credit item', function() {
        var agencyId = mockedAgency.id;
        var accountId = mockedAccount.id;

        var stateService = zemCreditsStateService.createInstance(
            agencyId,
            accountId
        );
        var state = stateService.getState();

        expect(state.agencyId).toEqual(agencyId);
        expect(state.accountId).toEqual(accountId);
        expect(state.hasAgencyScope).toEqual(true);
        expect(state.accounts).toEqual([mockedAccount]);
        expect(state.requests.reloadAccounts.inProgress).toEqual(false);

        var mockedCredit = {
            id: '123',
            agencyId: mockedAgency.id,
            accountId: null,
            status: CreditStatus.SIGNED,
            isReadOnly: false,
        };

        stateService.setCreditItem(mockedCredit);
        state = stateService.getState();

        expect(state.creditItem.status).toEqual(CreditStatus.SIGNED);
        expect(state.creditItemScopeState).toEqual(
            ScopeSelectorState.AGENCY_SCOPE
        );
        expect(state.creditItem.agencyId).toEqual(mockedAgency.id);
        expect(state.creditItem.accountId).toEqual(null);
        expect(state.creditItem.isReadOnly).toEqual(false);
    });

    it('should correctly clear credit item', function() {
        var agencyId = mockedAgency.id;
        var accountId = mockedAccount.id;

        var stateService = zemCreditsStateService.createInstance(
            agencyId,
            accountId
        );
        var state = stateService.getState();

        expect(state.agencyId).toEqual(agencyId);
        expect(state.accountId).toEqual(accountId);
        expect(state.hasAgencyScope).toEqual(true);
        expect(state.accounts).toEqual([mockedAccount]);
        expect(state.requests.reloadAccounts.inProgress).toEqual(false);

        var mockedCredit = {
            id: '123',
            agencyId: mockedAgency.id,
            accountId: null,
            status: CreditStatus.SIGNED,
            isReadOnly: false,
        };

        stateService.setCreditItem(mockedCredit);
        state = stateService.getState();

        expect(state.creditItem.status).toEqual(CreditStatus.SIGNED);
        expect(state.creditItemScopeState).toEqual(
            ScopeSelectorState.AGENCY_SCOPE
        );
        expect(state.creditItem.agencyId).toEqual(mockedAgency.id);
        expect(state.creditItem.accountId).toEqual(null);
        expect(state.creditItem.isReadOnly).toEqual(false);

        stateService.clearCreditItem();
        state = stateService.getState();

        expect(state.creditItem).toEqual({});
        expect(state.creditItemScopeState).toEqual(null);
        expect(state.requests.saveCreditItem).toEqual({});
    });
});
