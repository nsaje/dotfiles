angular.module('one.widgets').component('zemCloneContentModal', {
    bindings: {
        resolve: '<',
        modalInstance: '<',
    },
    templateUrl: '/app/widgets/zem-clone-content/components/zemCloneContentModal.component.html',
    controller: function (zemNavigationNewService, zemCloneContentService, zemSelectionService) {
        var $ctrl = this;

        $ctrl.submit = submit;
        $ctrl.navigate = navigate;

        $ctrl.requestInProgress = false;

        $ctrl.destinationAdGroupId = null;
        $ctrl.clonedContentState = null;
        $ctrl.destinationBatch = null;
        $ctrl.errors = null;

        function submit () {
            $ctrl.requestInProgress = true;

            zemCloneContentService.clone({
                adGroupId: $ctrl.resolve.adGroupId,
                selection: $ctrl.resolve.selection,
                destinationAdGroupId: $ctrl.destinationAdGroupId,
                state: $ctrl.clonedContentState
            }).then(function (data) {
                $ctrl.destinationBatch = data;
            }, function (errors) {
                $ctrl.errors = errors;
            }).finally(function () {
                $ctrl.requestInProgress = false;
            });
        }

        function navigate () {
            var navigationEntity = zemNavigationNewService.getEntityById(
                constants.entityType.AD_GROUP, $ctrl.destinationBatch.adGroup.id);

            return zemNavigationNewService
                .navigateTo(navigationEntity)
                .then(function () {
                    $ctrl.modalInstance.close();
                    zemSelectionService.setSelection({
                        batch: $ctrl.destinationBatch.id});
                });
        }
    }
});
