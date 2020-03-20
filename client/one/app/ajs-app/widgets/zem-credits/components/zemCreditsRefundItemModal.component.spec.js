var Currency = require('../../../../app.constants').Currency;
var CreditStatus = require('../../../../app.constants').CreditStatus;
var ScopeSelectorState = require('../../../../shared/components/scope-selector/scope-selector.constants')
    .ScopeSelectorState;

describe('component: zemCreditsRefundItemModal', function() {
    var $componentController;
    var $ctrl;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(inject(function(_$componentController_) {
        $componentController = _$componentController_;
    }));

    it('should be correctly initialized with agency scope', function() {
        var bindings = {
            close: angular.noop,
            resolve: {
                stateService: {
                    getState: function() {
                        return {
                            agencyId: '123',
                            accountId: null,
                            accounts: [
                                {
                                    id: '345',
                                    name: 'USD Account',
                                    currency: Currency.USD,
                                },
                                {
                                    id: '678',
                                    name: 'EUR Account',
                                    currency: Currency.EUR,
                                },
                            ],
                            hasAgencyScope: true,
                            creditItemScopeState:
                                ScopeSelectorState.AGENCY_SCOPE,
                            creditItem: {
                                id: '123',
                                agencyId: '123',
                                accountId: null,
                                status: CreditStatus.SIGNED,
                                currency: Currency.USD,
                                isSigned: true,
                                isCanceled: false,
                            },
                            creditRefundItem: {
                                accountId: null,
                            },
                            requests: {
                                saveCreditItem: {},
                            },
                        };
                    },
                },
            },
        };
        $ctrl = $componentController('zemCreditsRefundItemModal', {}, bindings);
        $ctrl.$onInit();

        expect($ctrl.mediaAmount).toEqual(0);
        expect($ctrl.accounts).toEqual([
            {
                id: '345',
                name: 'USD Account',
                currency: Currency.USD,
            },
        ]);
        expect($ctrl.selectedAccount).toEqual(null);
        expect($ctrl.isAccountSelectDisabled).toEqual(false);
    });

    it('should be correctly initialized with account scope', function() {
        var bindings = {
            close: angular.noop,
            resolve: {
                stateService: {
                    getState: function() {
                        return {
                            agencyId: '123',
                            accountId: '678',
                            accounts: [
                                {
                                    id: '345',
                                    name: 'USD Account',
                                    currency: Currency.USD,
                                },
                                {
                                    id: '678',
                                    name: 'EUR Account',
                                    currency: Currency.EUR,
                                },
                            ],
                            hasAgencyScope: false,
                            creditItemScopeState:
                                ScopeSelectorState.ACCOUNT_SCOPE,
                            creditItem: {
                                id: '123',
                                agencyId: null,
                                accountId: '678',
                                status: CreditStatus.SIGNED,
                                currency: Currency.EUR,
                                isSigned: true,
                                isCanceled: false,
                            },
                            creditRefundItem: {
                                accountId: '678',
                            },
                            requests: {
                                saveCreditItem: {},
                            },
                        };
                    },
                },
            },
        };
        $ctrl = $componentController('zemCreditsRefundItemModal', {}, bindings);
        $ctrl.$onInit();

        expect($ctrl.mediaAmount).toEqual(0);
        expect($ctrl.accounts).toEqual([
            {
                id: '678',
                name: 'EUR Account',
                currency: Currency.EUR,
            },
        ]);
        expect($ctrl.selectedAccount).toEqual({
            id: '678',
            name: 'EUR Account',
            currency: Currency.EUR,
        });
        expect($ctrl.isAccountSelectDisabled).toEqual(true);
    });
});
