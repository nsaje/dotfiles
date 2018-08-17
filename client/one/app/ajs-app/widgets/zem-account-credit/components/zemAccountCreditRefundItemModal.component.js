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
            $ctrl.mediaAmount = 0;
            $ctrl.stateService = $ctrl.resolve.stateService;
            $ctrl.state = $ctrl.stateService.getState();
            $ctrl.openDatePicker = openDatePicker;
            $ctrl.saveCreditRefundItem = saveCreditRefundItem;
            $ctrl.discardCreditRefundItem = discardCreditRefundItem;
            $ctrl.calculateTotalAmount = calculateTotalAmount;

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
            var now = moment(Date.now());
            $ctrl.datePickerOptions = {
                datepickerMode: 'month',
                minMode: 'month',
                minDate: now.subtract(1, 'month').toDate(),
                maxDate: now.toDate(),
            };
        }

        function openDatePicker() {
            $ctrl.isDatePickerOpen = true;
        }

        function saveCreditRefundItem() {
            if ($ctrl.state.requests.saveCreditRefundItem.inProgress) return;
            $ctrl.state.creditRefundItem.amount = calculateTotalAmount();
            $ctrl.stateService.saveCreditRefundItem().then(function() {
                $ctrl.saved = true;
                closeModal();
            });
        }

        function calculateTotalAmount() {
            var media = $ctrl.mediaAmount || 0,
                fee = parseFloat($ctrl.state.creditItem.licenseFee) / 100,
                margin =
                    ($ctrl.state.creditRefundItem.effectiveMargin || 0) / 100;
            return Math.ceil(media / (1 - fee) / (1 - margin));
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
