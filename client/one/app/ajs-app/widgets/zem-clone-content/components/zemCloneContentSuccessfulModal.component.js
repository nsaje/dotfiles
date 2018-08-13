angular.module('one.widgets').component('zemCloneContentSuccessfulModal', {
    bindings: {
        resolve: '<',
        modalInstance: '<',
    },
    template: require('./zemCloneContentSuccessfulModal.component.html'),
    controller: function($q, zemNavigationNewService, zemSelectionService) {
        var $ctrl = this;

        $ctrl.navigateTo = navigateTo;

        function navigateTo() {
            $ctrl.modalInstance.close();

            var navigationEntity = zemNavigationNewService.getEntityById(
                constants.entityType.AD_GROUP,
                $ctrl.resolve.destinationBatch.adGroup.id
            );
            return zemNavigationNewService
                .navigateTo(navigationEntity)
                .then(function() {
                    zemSelectionService.setSelection({
                        batch: parseInt($ctrl.resolve.destinationBatch.id),
                    });
                });
        }
    },
});
