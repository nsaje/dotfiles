angular.module('one.widgets').component('zemCloneContentModal', {
    bindings: {
        resolve: '<',
        modalInstance: '<',
    },
    templateUrl: '/app/widgets/zem-clone-content/components/zemCloneContentModal.component.html',
    controller: function ($q, zemNavigationNewService, zemCloneContentService, zemSelectionService, zemSelectDataStore) { //eslint-disable-line max-len
        var $ctrl = this;
        $ctrl.texts = {
            placeholder: 'Search ad group ...'
        };

        //
        // Public
        //
        $ctrl.submit = submit;
        $ctrl.onAdGroupSelected = onAdGroupSelected;

        //
        // Private
        //
        $ctrl.adGroup = null;
        $ctrl.destinationAdGroupId = null;
        $ctrl.clonedContentState = null;

        $ctrl.errors = null;
        $ctrl.requestInProgress = false;

        $ctrl.$onInit = function () {
            $ctrl.store = getDataStore();
            zemNavigationNewService.getNavigationHierarchyPromise().then(function () {
                $ctrl.adGroup = zemNavigationNewService.getEntityById(
                    constants.entityType.AD_GROUP, $ctrl.resolve.adGroupId);
            });
        };

        function submit () {
            $ctrl.requestInProgress = true;

            zemCloneContentService.clone({
                adGroupId: $ctrl.resolve.adGroupId,
                selection: $ctrl.resolve.selection,
                destinationAdGroupId: $ctrl.destinationAdGroupId,
                state: $ctrl.clonedContentState
            }).then(function (data) {
                $ctrl.modalInstance.close(data);
                zemCloneContentService.openResultsModal($ctrl.adGroup, data);
            }, function (errors) {
                $ctrl.errors = errors;
            }).finally(function () {
                $ctrl.requestInProgress = false;
            });
        }

        // zem UI select properties
        //

        function getDataStore () {
            var promise = zemNavigationNewService.getNavigationHierarchyPromise().then(function () {
                return getDataStoreItems();
            });

            return zemSelectDataStore.createInstance(promise);
        }

        function getDataStoreItems () {
            var adGroups = [];
            angular.forEach(zemNavigationNewService.getNavigationHierarchy().ids.adGroups, function (value) {
                if (!value.data.archived) {
                    adGroups.push({
                        id: value.id,
                        name: value.name,
                        h1: value.parent.parent.name,
                        h2: value.parent.name,
                        searchableName: value.parent.parent.name + ' ' + value.parent.name + ' ' + value.name,
                    });
                }
            });
            return adGroups;
        }

        function onAdGroupSelected (item) {
            $ctrl.destinationAdGroupId = item ? item.id : null;
        }
    }
});
