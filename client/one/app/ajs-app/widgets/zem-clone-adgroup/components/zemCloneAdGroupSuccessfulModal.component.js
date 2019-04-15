angular.module('one.widgets').component('zemCloneAdGroupSuccessfulModal', {
    bindings: {
        resolve: '<',
        modalInstance: '<',
    },
    template: require('./zemCloneAdGroupSuccessfulModal.component.html'),
    controller: function(zemNavigationNewService) {
        var $ctrl = this;

        $ctrl.navigateTo = navigateTo;

        function navigateTo() {
            $ctrl.modalInstance.close();
            return zemNavigationNewService
                .getEntityById(
                    constants.entityType.AD_GROUP,
                    $ctrl.resolve.destinationAdGroup.id
                )
                .then(function(navigationEntity) {
                    zemNavigationNewService.navigateTo(navigationEntity, {
                        settings: 'create',
                    });
                });
        }
    },
});
