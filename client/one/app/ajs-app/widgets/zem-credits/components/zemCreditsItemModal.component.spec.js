var Currency = require('../../../../app.constants').Currency;
var CreditStatus = require('../../../../app.constants').CreditStatus;
var ScopeSelectorState = require('../../../../shared/components/scope-selector/scope-selector.constants')
    .ScopeSelectorState;
var CURRENCIES = require('../../../../app.config').CURRENCIES;
var currencyHelpers = require('../../../../shared/helpers/currency.helpers');

describe('component: zemCreditsItemModal', function() {
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
                                agencyId: '123',
                                accountId: null,
                                status: CreditStatus.PENDING,
                                isSigned: false,
                                isCanceled: false,
                            },
                            requests: {
                                saveCreditItem: {},
                            },
                        };
                    },
                    reloadCreditItemBudgets: function() {
                        return [];
                    },
                },
            },
        };

        $ctrl = $componentController('zemCreditsItemModal', {}, bindings);
        $ctrl.$onInit();

        expect($ctrl.currency).toEqual(Currency.USD);
        expect($ctrl.CURRENCIES).toEqual(CURRENCIES);
        expect($ctrl.selectedCurrency).toEqual({
            name: 'US Dollar',
            value: Currency.USD,
        });
        expect($ctrl.currencySymbol).toEqual(
            currencyHelpers.getCurrencySymbol($ctrl.currency)
        );
        expect($ctrl.accounts).toEqual([
            {
                id: '345',
                name: 'USD Account',
                currency: Currency.USD,
            },
        ]);
        expect($ctrl.createMode).toEqual(true);
        expect($ctrl.wasSigned).toEqual(false);
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
                                agencyId: null,
                                accountId: '678',
                                status: CreditStatus.PENDING,
                                isSigned: false,
                                isCanceled: false,
                            },
                            requests: {
                                saveCreditItem: {},
                            },
                        };
                    },
                    reloadCreditItemBudgets: function() {
                        return [];
                    },
                },
            },
        };

        $ctrl = $componentController('zemCreditsItemModal', {}, bindings);
        $ctrl.$onInit();

        expect($ctrl.currency).toEqual(Currency.EUR);
        expect($ctrl.CURRENCIES).toEqual(CURRENCIES);
        expect($ctrl.selectedCurrency).toEqual({
            name: 'Euro',
            value: Currency.EUR,
        });
        expect($ctrl.currencySymbol).toEqual(
            currencyHelpers.getCurrencySymbol($ctrl.currency)
        );
        expect($ctrl.accounts).toEqual([
            {
                id: '678',
                name: 'EUR Account',
                currency: Currency.EUR,
            },
        ]);
        expect($ctrl.createMode).toEqual(true);
        expect($ctrl.wasSigned).toEqual(false);
    });
});
