angular.module('one.widgets').component('zemCloneContentModal', {
    bindings: {
        resolve: '<',
        modalInstance: '<',
    },
    templateUrl: '/app/widgets/zem-clone-content/components/zemCloneContentModal.component.html',
    controller: function ($q, zemNavigationNewService, zemCloneContentService, zemSelectionService, zemSelectDataStore) { //eslint-disable-line max-len
        var $ctrl = this;

        $ctrl.submit = submit;
        $ctrl.navigate = navigate;
        $ctrl.onAdGroupSelected = onAdGroupSelected;

        $ctrl.requestInProgress = false;
        $ctrl.texts = {
            placeholder: 'Select Ad group to clone to ...'
        };

        $ctrl.destinationAdGroupId = $ctrl.resolve.adGroup.id;
        $ctrl.destinationBatch = null;
        $ctrl.clonedContentState = null;
        $ctrl.errors = null;

        $ctrl.$onInit = function () {
            $ctrl.store = getDataStore();
        };

        function submit () {
            $ctrl.requestInProgress = true;

            zemCloneContentService.clone({
                adGroupId: $ctrl.resolve.adGroup.id,
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

        function getDataStore () {
            var promise;

            if (zemNavigationNewService.getNavigationHierarchy()) {
                promise = $q.resolve(getDataStoreItems());
            } else {
                var deferred = $q.defer();
                zemNavigationNewService.onHierarchyUpdate(function () {
                    deferred.resolve(getDataStoreItems());
                });
                promise = deferred.promise;
            }

            return zemSelectDataStore.createInstance(promise);
        }

        function getDataStoreItems () {
            var adGroups = [];
            angular.forEach(zemNavigationNewService.getNavigationHierarchy().ids.adGroups, function (value) {
                adGroups.push({
                    id: value.id,
                    name: value.name,
                    h1: value.parent.parent.name,
                    h2: value.parent.name,
                    searchableName: value.parent.parent.name + ' ' + value.parent.name + ' ' + value.name,
                });
            });
            return adGroups;
        }

        function onAdGroupSelected (item) {
            $ctrl.destinationAdGroupId = item ? item.id : null;
        }
    }
});
