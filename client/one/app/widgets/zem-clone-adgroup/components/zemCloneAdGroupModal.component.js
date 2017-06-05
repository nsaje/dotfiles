angular.module('one.widgets').component('zemCloneAdGroupModal', {
    bindings: {
        resolve: '<',
        modalInstance: '<',
    },
    templateUrl: '/app/widgets/zem-clone-adgroup/components/zemCloneAdGroupModal.component.html',
    controller: function ($q, zemNavigationNewService, zemCloneAdGroupService, zemSelectDataStore) {
        var $ctrl = this;
        $ctrl.texts = {
            placeholder: 'Select Campaign to clone to ...'
        };

        //
        // Public
        //
        $ctrl.submit = submit;
        $ctrl.onCampaignSelected = onCampaignSelected;

        //
        // Private
        //
        $ctrl.destinationCampaignId = $ctrl.resolve.campaign.id;
        $ctrl.destinationAdGroup = null;

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

            zemCloneAdGroupService.clone({
                adGroupId: $ctrl.resolve.adGroup.id,
                destinationCampaignId: $ctrl.destinationCampaignId,
            }).then(function (data) {
                zemCloneAdGroupService.openResultsModal(data);
                $ctrl.modalInstance.close();
            }, function (errors) {
                $ctrl.errors = errors;
            }).finally(function () {
                $ctrl.requestInProgress = false;
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
            var campaigns = [];
            angular.forEach(zemNavigationNewService.getNavigationHierarchy().ids.campaigns, function (value) {
                campaigns.push({
                    id: value.id,
                    name: value.name,
                    h1: value.parent.name,
                    searchableName: value.parent.name + ' ' + value.name,
                });

            });
            return campaigns;
        }

        function onCampaignSelected (item) {
            $ctrl.destinationCampaignId = item ? item.id : null;
        }
    }
});
