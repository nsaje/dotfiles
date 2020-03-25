var commonHelpers = require('../../../../shared/helpers/common.helpers');
var arrayHelpers = require('../../../../shared/helpers/array.helpers');
var currencyHelpers = require('../../../../shared/helpers/currency.helpers');
var CURRENCIES = require('../../../../app.config').CURRENCIES;
var ScopeSelectorState = require('../../../../shared/components/scope-selector/scope-selector.constants')
    .ScopeSelectorState;

angular.module('one').component('zemCreditsItemModal', {
    bindings: {
        close: '&',
        resolve: '<',
    },
    template: require('./zemCreditsItemModal.component.html'),
    controller: function() {
        var $ctrl = this;

        $ctrl.openStartDatePicker = openStartDatePicker;
        $ctrl.openEndDatePicker = openEndDatePicker;
        $ctrl.getLicenseFees = getLicenseFees;
        $ctrl.saveCreditItem = saveCreditItem;
        $ctrl.discardCreditItem = discardCreditItem;
        $ctrl.onScopeStateChange = onScopeStateChange;
        $ctrl.onAccountChange = onAccountChange;
        $ctrl.onSelectedCurrencyChange = onSelectedCurrencyChange;

        $ctrl.$onInit = function() {
            $ctrl.stateService = $ctrl.resolve.stateService;
            $ctrl.state = $ctrl.stateService.getState();

            $ctrl.CURRENCIES = CURRENCIES;
            $ctrl.selectedCurrency = getSelectedCurrency(
                $ctrl.CURRENCIES,
                $ctrl.state.creditItem.currency
            );

            $ctrl.currencySymbol = currencyHelpers.getCurrencySymbol(
                $ctrl.state.creditItem.currency
            );

            $ctrl.accounts = getAccountsForCurrency(
                $ctrl.state.accounts,
                $ctrl.state.creditItem.currency
            );

            $ctrl.wasSigned = $ctrl.state.creditItem.isSigned;
            $ctrl.createMode = !commonHelpers.isDefined(
                $ctrl.state.creditItem.id
            );

            $ctrl.startDatePickerOptions = {minDate: moment().toDate()};
            $ctrl.isStartDatePickerOpen = false;

            $ctrl.endDatePickerOptions = {
                minDate: commonHelpers.isDefined($ctrl.state.creditItem.endDate)
                    ? $ctrl.state.creditItem.endDate
                    : moment().toDate(),
            };
            $ctrl.isEndDatePickerOpen = false;

            if (!$ctrl.createMode) {
                $ctrl.stateService.reloadCreditItemBudgets();
            }
        };

        $ctrl.$onDestroy = function() {
            $ctrl.stateService.clearCreditItem();
        };

        function openStartDatePicker() {
            $ctrl.isStartDatePickerOpen = true;
        }

        function openEndDatePicker() {
            $ctrl.isEndDatePickerOpen = true;
        }

        function getLicenseFees(search, additional) {
            // Use fresh instance because we modify the collection on the fly
            var fees = ['15.00', '20.00', '25.00'];
            if (additional) {
                if (fees.indexOf(additional) === -1) {
                    fees.push(additional);
                }
                fees.sort();
            }
            // Adds the searched for value to the array
            if (search && fees.indexOf(search) === -1) {
                fees.unshift(search);
            }

            return fees;
        }

        function saveCreditItem() {
            if ($ctrl.state.requests.saveCreditItem.inProgress) return;
            $ctrl.stateService.saveCreditItem().then(function() {
                closeModal();
            });
        }

        function discardCreditItem() {
            closeModal();
        }

        function closeModal() {
            $ctrl.close();
        }

        function onSelectedCurrencyChange() {
            $ctrl.state.creditItem.currency = $ctrl.selectedCurrency.value;
            $ctrl.currencySymbol = currencyHelpers.getCurrencySymbol(
                $ctrl.state.creditItem.currency
            );
            $ctrl.accounts = getAccountsForCurrency(
                $ctrl.state.accounts,
                $ctrl.state.creditItem.currency
            );
            $ctrl.state.creditItem.accountId = null;
        }

        function onScopeStateChange($event) {
            $ctrl.state.creditItemScopeState = $event;
            $ctrl.state.creditItem.agencyId =
                $ctrl.state.creditItemScopeState ===
                ScopeSelectorState.AGENCY_SCOPE
                    ? $ctrl.state.agencyId
                    : null;
            $ctrl.state.creditItem.accountId =
                $ctrl.state.creditItemScopeState ===
                ScopeSelectorState.ACCOUNT_SCOPE
                    ? commonHelpers.getValueOrDefault(
                          $ctrl.state.accountId,
                          $ctrl.accounts[0].id
                      )
                    : null;
        }

        function onAccountChange($event) {
            $ctrl.state.creditItem.accountId = $event;
        }

        function getAccountsForCurrency(accounts, currency) {
            if (
                !arrayHelpers.isEmpty(accounts) &&
                commonHelpers.isDefined(currency)
            ) {
                return accounts.filter(function(account) {
                    return account.currency === currency;
                });
            }
            return accounts;
        }

        function getSelectedCurrency(currencies, currency) {
            if (
                !arrayHelpers.isEmpty(currencies) &&
                commonHelpers.isDefined(currency)
            ) {
                return currencies.filter(function(item) {
                    return item.value === currency;
                })[0];
            }
            return null;
        }
    },
});
