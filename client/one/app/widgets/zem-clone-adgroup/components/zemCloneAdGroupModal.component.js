angular.module('one.widgets').component('zemCloneAdGroupModal', {
    bindings: {
        resolve: '<',
        modalInstance: '<',
    },
    templateUrl: '/app/widgets/zem-clone-adgroup/components/zemCloneAdGroupModal.component.html',
    controller: function (zemNavigationNewService, zemCloneAdGroupService) {
        var $ctrl = this;

        $ctrl.submit = submit;
        $ctrl.navigate = navigate;

        $ctrl.requestInProgress = false;

        $ctrl.destinationCampaignId = null;
        $ctrl.destinationAdGroup = null;
        $ctrl.errors = null;

        function submit () {
            $ctrl.requestInProgress = true;

            zemCloneAdGroupService.clone({
                adGroupId: $ctrl.resolve.adGroup.id,
                destinationCampaignId: $ctrl.destinationCampaignId,
            }).then(function (data) {
                $ctrl.destinationAdGroup = data;
            }, function (errors) {
                $ctrl.errors = errors;
            }).finally(function () {
                $ctrl.requestInProgress = false;
            });
        }

        function navigate () {
            var navigationEntity = zemNavigationNewService.getEntityById(
                constants.entityType.AD_GROUP, $ctrl.destinationAdGroup.id);

            return zemNavigationNewService.navigateTo(navigationEntity).then(function () {
                $ctrl.modalInstance.close();
            });
        }
    }
});
