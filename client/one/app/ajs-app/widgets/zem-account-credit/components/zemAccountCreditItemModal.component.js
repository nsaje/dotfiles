angular.module('one').component('zemAccountCreditItemModal', {
    bindings: {
        close: '&',
        resolve: '<',
    },
    template: require('./zemAccountCreditItemModal.component.html'),
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

            $ctrl.openStartDatePicker = openStartDatePicker;
            $ctrl.openEndDatePicker = openEndDatePicker;
            $ctrl.getLicenseFees = getLicenseFees;
            $ctrl.saveCreditItem = saveCreditItem;
            $ctrl.discardCreditItem = discardCreditItem;

            updateView();
        };

        $ctrl.$onDestroy = function() {
            $ctrl.stateService.clearCreditItem();
        };

        function updateView() {
            var currentMoment = moment();
            $ctrl.createMode = $ctrl.resolve.id ? false : true;
            $ctrl.account = $ctrl.resolve.account;
            $ctrl.newCreditCurrencySymbol = zemMulticurrencyService.getAppropriateCurrencySymbol(
                $ctrl.account
            );
            $ctrl.startDatePickerOptions = {minDate: currentMoment.toDate()};
            $ctrl.endDatePickerOptions = {minDate: currentMoment.toDate()};
            $ctrl.isStartDatePickerOpen = false;
            $ctrl.isEndDatePickerOpen = false;

            if ($ctrl.createMode) {
                $ctrl.stateService.createNewCreditItem(currentMoment);
            } else {
                $ctrl.stateService
                    .reloadCreditItem($ctrl.resolve.id)
                    .then(function() {
                        $ctrl.wasSigned = $ctrl.state.creditItem.isSigned;
                        $ctrl.endDatePickerOptions = {
                            minDate: $ctrl.state.creditItem.endDate,
                        };
                    });
            }
        }

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

            $ctrl.stateService
                .saveCreditItem($ctrl.createMode)
                .then(function() {
                    $ctrl.saved = true;
                    closeModal();
                });
        }

        function discardCreditItem() {
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
