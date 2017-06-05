angular.module('one.widgets').component('zemCloneAdGroupSuccessfulModal', {
    bindings: {
        resolve: '<',
        modalInstance: '<',
    },
    templateUrl: '/app/widgets/zem-clone-adgroup/components/zemCloneAdGroupSuccessfulModal.component.html',
    controller: function (zemNavigationNewService) {
        var $ctrl = this;

        $ctrl.navigate = navigate;

        function navigate () {
            var navigationEntity = zemNavigationNewService.getEntityById(
                constants.entityType.AD_GROUP, $ctrl.resolve.destinationAdGroup.id);

            return zemNavigationNewService.navigateTo(navigationEntity).then(function () {
                $ctrl.modalInstance.close();
            });
        }
    }
});
