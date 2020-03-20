require('./zemCredits.component.less');

angular.module('one').component('zemCredits', {
    bindings: {
        agencyId: '<',
        accountId: '<',
    },
    template: require('./zemCredits.component.html'),
    controller: function(
        zemCreditsStateService,
        zemPermissions,
        $window,
        $uibModal
    ) {
        var $ctrl = this;

        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.openCreditItemModal = openCreditItemModal;
        $ctrl.cancelCreditItem = cancelCreditItem;
        $ctrl.openCreditRefundItemModal = openCreditRefundItemModal;

        $ctrl.$onChanges = function(changes) {
            if (changes.agencyId || changes.accountId) {
                $ctrl.stateService = zemCreditsStateService.createInstance(
                    $ctrl.agencyId,
                    $ctrl.accountId
                );
                $ctrl.stateService.reload();
                $ctrl.state = $ctrl.stateService.getState();
            }
        };

        function cancelCreditItem(creditItem) {
            if (
                !$window.confirm(
                    'Are you sure you want to cancel the credit line item?'
                )
            ) {
                return;
            }
            $ctrl.stateService.cancelCreditItem(creditItem);
        }

        function openCreditItemModal(creditItem) {
            $ctrl.stateService.setCreditItem(creditItem);
            $uibModal.open({
                component: 'zemCreditsItemModal',
                windowClass: 'zem-credits-item-modal',
                resolve: {
                    stateService: $ctrl.stateService,
                },
            });
        }

        function openCreditRefundItemModal(creditItem) {
            $ctrl.stateService.setCreditItem(creditItem);
            $ctrl.stateService.setCreditRefundItem({});
            $uibModal.open({
                component: 'zemCreditsRefundItemModal',
                windowClass: 'zem-credits-refund-item-modal',
                resolve: {
                    stateService: $ctrl.stateService,
                },
            });
        }
    },
});
