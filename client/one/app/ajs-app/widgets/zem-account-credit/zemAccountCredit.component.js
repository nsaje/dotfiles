require('./zemAccountCredit.component.less');

angular.module('one').component('zemAccountCredit', {
    bindings: {
        account: '<',
    },
    template: require('./zemAccountCredit.component.html'),
    controller: function(
        zemAccountCreditStateService,
        zemPermissions,
        $window,
        $uibModal
    ) {
        var $ctrl = this;

        $ctrl.hasPermission = zemPermissions.hasPermission;

        $ctrl.$onInit = function() {
            $ctrl.stateService = zemAccountCreditStateService.createInstance(
                $ctrl.account
            );
            $ctrl.stateService.reloadCredit();
            $ctrl.state = $ctrl.stateService.getState();

            $ctrl.openCreditItemModal = openCreditItemModal;
            $ctrl.cancelCreditItem = cancelCreditItem;
            $ctrl.openCreditRefundItemModal = openCreditRefundItemModal;
        };

        function cancelCreditItem(id) {
            if (
                !$window.confirm(
                    'Are you sure you want to cancel the credit line item?'
                )
            ) {
                return;
            }
            $ctrl.stateService.cancelCreditItem(id);
        }

        function openCreditItemModal(id) {
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

        function openCreditRefundItemModal(creditItem) {
            $ctrl.stateService.setCreditItem(creditItem);
            $uibModal.open({
                component: 'zemAccountCreditRefundItemModal',
                windowClass: 'zem-account-credit-refund-item-modal',
                resolve: {
                    stateService: $ctrl.stateService,
                    account: $ctrl.account,
                },
            });
        }
    },
});
