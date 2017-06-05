angular.module('one.widgets').component('zemCloneContentModal', {
    bindings: {
        resolve: '<',
        modalInstance: '<',
    },
    templateUrl: '/app/widgets/zem-clone-content/components/zemCloneContentModal.component.html',
    controller: function ($q, zemNavigationNewService, zemCloneContentService, zemSelectionService, zemSelectDataStore) { //eslint-disable-line max-len
        var $ctrl = this;
        $ctrl.texts = {
            placeholder: 'Select Ad group to clone to ...'
        };

        //
        // Public
        //
        $ctrl.submit = submit;
        $ctrl.onAdGroupSelected = onAdGroupSelected;

        //
        // Private
        //
        $ctrl.destinationAdGroupId = $ctrl.resolve.adGroup.id;
        $ctrl.destinationBatch = null;
        $ctrl.clonedContentState = null;

        $ctrl.errors = null;
        $ctrl.requestInProgress = false;

        $ctrl.$onInit = function () {
            $ctrl.store = getDataStore();
        };

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
                zemCloneContentService.openResultsModal(data);
                $ctrl.modalInstance.close();
            }, function (errors) {
                $ctrl.errors = errors;
            }).finally(function () {
                $ctrl.requestInProgress = false;
            });
        }

        // zem UI select properties
        //

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
