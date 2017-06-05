angular.module('one.widgets').component('zemCloneAdGroupModal', {
    bindings: {
        resolve: '<',
        modalInstance: '<',
    },
    templateUrl: '/app/widgets/zem-clone-adgroup/components/zemCloneAdGroupModal.component.html',
    controller: function ($q, zemNavigationNewService, zemCloneAdGroupService, zemSelectDataStore) {
        var $ctrl = this;

        $ctrl.submit = submit;
        $ctrl.navigate = navigate;
        $ctrl.onCampaignSelected = onCampaignSelected;

        $ctrl.requestInProgress = false;

        $ctrl.destinationCampaignId = $ctrl.resolve.campaign.id;
        $ctrl.destinationAdGroup = null;
        $ctrl.errors = null;

        $ctrl.$onInit = function () {
            $ctrl.store = getDataStore();
        };

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
