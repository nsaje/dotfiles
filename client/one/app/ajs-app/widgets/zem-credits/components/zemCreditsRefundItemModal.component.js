var arrayHelpers = require('../../../../shared/helpers/array.helpers');
var commonHelpers = require('../../../../shared/helpers/common.helpers');
var ScopeSelectorState = require('../../../../shared/components/scope-selector/scope-selector.constants')
    .ScopeSelectorState;

angular.module('one').component('zemCreditsRefundItemModal', {
    bindings: {
        close: '&',
        resolve: '<',
    },
    template: require('./zemCreditsRefundItemModal.component.html'),
    controller: function() {
        var $ctrl = this;

        $ctrl.openDatePicker = openDatePicker;
        $ctrl.saveCreditRefundItem = saveCreditRefundItem;
        $ctrl.discardCreditRefundItem = discardCreditRefundItem;
        $ctrl.calculateTotalAmount = calculateTotalAmount;
        $ctrl.onSelectedAccountChange = onSelectedAccountChange;

        $ctrl.$onInit = function() {
            $ctrl.stateService = $ctrl.resolve.stateService;
            $ctrl.state = $ctrl.stateService.getState();

            $ctrl.mediaAmount = 0;

            $ctrl.accounts = getAccountsForCurrency(
                $ctrl.state.accounts,
                $ctrl.state.creditItem.currency
            );
            $ctrl.selectedAccount = getSelectedAccount(
                $ctrl.accounts,
                $ctrl.state.creditRefundItem.accountId
            );
            $ctrl.isAccountSelectDisabled =
                $ctrl.state.creditItemScopeState ===
                ScopeSelectorState.ACCOUNT_SCOPE;

            $ctrl.isDatePickerOpen = false;
            var now = moment(Date.now());
            $ctrl.datePickerOptions = {
                datepickerMode: 'month',
                minMode: 'month',
                minDate: now
                    .clone()
                    .subtract(1, 'month')
                    .startOf('month')
                    .toDate(),
                maxDate: now
                    .clone()
                    .endOf('month')
                    .toDate(),
            };
        };

        $ctrl.$onDestroy = function() {
            $ctrl.stateService.clearCreditRefundItem();
        };

        function onSelectedAccountChange() {
            $ctrl.state.creditRefundItem.accountId = $ctrl.selectedAccount.id;
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

        function getSelectedAccount(accounts, accountId) {
            if (
                !arrayHelpers.isEmpty(accounts) &&
                commonHelpers.isDefined(accountId)
            ) {
                return accounts.filter(function(account) {
                    return account.id === accountId;
                })[0];
            }
            return null;
        }

        function openDatePicker() {
            $ctrl.isDatePickerOpen = true;
        }

        function saveCreditRefundItem() {
            if ($ctrl.state.requests.saveCreditRefundItem.inProgress) return;
            $ctrl.state.creditRefundItem.amount = calculateTotalAmount();
            $ctrl.stateService.saveCreditRefundItem().then(function() {
                closeModal();
            });
        }

        function calculateTotalAmount() {
            var mediaAmount = $ctrl.mediaAmount || 0;
            var licenseFee =
                parseFloat($ctrl.state.creditItem.licenseFee || 0) / 100;
            var margin =
                parseFloat($ctrl.state.creditRefundItem.effectiveMargin || 0) /
                100;
            return Math.ceil(mediaAmount / (1 - licenseFee) / (1 - margin));
        }

        function discardCreditRefundItem() {
            closeModal();
        }

        function closeModal() {
            $ctrl.close();
        }
    },
});
