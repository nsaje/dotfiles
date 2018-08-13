angular.module('one').component('zemAccountCreditRefundItemModal', {
    bindings: {
        close: '&',
        resolve: '<',
    },
    template: require('./zemAccountCreditRefundItemModal.component.html'),
    controller: function(
        zemUserService,
        $filter,
        $timeout,
        zemMulticurrencyService
    ) {
        var $ctrl = this;

        $ctrl.$onInit = function() {
            $ctrl.stateService = $ctrl.resolve.stateService;
            $ctrl.state = $ctrl.stateService.getState();
            $ctrl.openDatePicker = openDatePicker;
            $ctrl.saveCreditRefundItem = saveCreditRefundItem;
            $ctrl.discardCreditRefundItem = discardCreditRefundItem;

            updateView();
        };

        $ctrl.$onDestroy = function() {
            $ctrl.stateService.clearCreditRefundItem();
        };

        function updateView() {
            $ctrl.account = $ctrl.resolve.account;
            $ctrl.newCreditRefundCurrencySymbol = zemMulticurrencyService.getAppropriateCurrencySymbol(
                $ctrl.account
            );
            $ctrl.isDatePickerOpen = false;

            $ctrl.datePickerOptions = {
                datepickerMode: 'month',
                minMode: 'month',
                minDate: $ctrl.state.creditItem.startDate,
                maxDate: $ctrl.state.creditItem.endDate,
            };
        }

        function openDatePicker() {
            $ctrl.isDatePickerOpen = true;
        }

        function saveCreditRefundItem() {
            if ($ctrl.state.requests.saveCreditRefundItem.inProgress) return;

            $ctrl.stateService.saveCreditRefundItem().then(function() {
                $ctrl.saved = true;
                closeModal();
            });
        }

        function discardCreditRefundItem() {
            $ctrl.discarded = true;
            closeModal();
        }

        function closeModal() {
            $timeout(function() {
                $ctrl.close();
            }, 1000);
        }
    },
});
