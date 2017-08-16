require('./zemAccountCredit.component.less');

angular.module('one').component('zemAccountCredit', {
    bindings: {
        account: '<',
    },
    template: require('./zemAccountCredit.component.html'),
    controller: function (zemAccountCreditStateService, $window, $uibModal) {
        var $ctrl = this;

        $ctrl.$onInit = function () {
            $ctrl.stateService = zemAccountCreditStateService.createInstance($ctrl.account);
            $ctrl.stateService.reloadCredit();
            $ctrl.state = $ctrl.stateService.getState();

            $ctrl.openCreditItemModal = openCreditItemModal;
            $ctrl.cancelCreditItem = cancelCreditItem;
        };

        function cancelCreditItem (id) {
            if (!$window.confirm('Are you sure you want to cancel the credit line item?')) {
                return;
            }
            $ctrl.stateService.cancelCreditItem(id);
        }

        function openCreditItemModal (id) {
            $uibModal.open({
                component: 'zemAccountCreditItemModal',
                windowClass: 'zem-account-credit-item-modal',
                resolve: {
                    stateService: $ctrl.stateService,
                    id: id,
                    account: $ctrl.account,
                },
            });
        }
    },
});
