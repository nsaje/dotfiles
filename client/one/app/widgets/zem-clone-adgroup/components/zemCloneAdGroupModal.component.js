angular.module('one.widgets').component('zemCloneAdGroupModal', {
    bindings: {
        resolve: '<',
        modalInstance: '<',
    },
    templateUrl: '/app/widgets/zem-clone-adgroup/components/zemCloneAdGroupModal.component.html',
    controller: function ($q, zemNavigationService, zemNavigationNewService, zemCloneAdGroupService, zemSelectDataStore, zemEntityService) { // eslint-disable-line max-len
        var $ctrl = this;
        $ctrl.texts = {
            placeholder: 'Search campaign ...'
        };

        //
        // Public
        //
        $ctrl.submit = submit;
        $ctrl.onCampaignSelected = onCampaignSelected;

        //
        // Private
        //
        $ctrl.campaign = null;
        $ctrl.adGroup = null;
        $ctrl.destinationCampaignId = null;

        $ctrl.errors = null;
        $ctrl.requestInProgress = false;

        $ctrl.$onInit = function () {
            $ctrl.store = getDataStore();
            zemNavigationNewService.getNavigationHierarchyPromise().then(function () {
                $ctrl.campaign = zemNavigationNewService.getEntityById(
                    constants.entityType.CAMPAIGN, $ctrl.resolve.campaignId);
                $ctrl.adGroup = zemNavigationNewService.getEntityById(
                    constants.entityType.AD_GROUP, $ctrl.resolve.adGroupId);
            });
        };

        function submit () {
            $ctrl.requestInProgress = true;

            zemEntityService.cloneEntity(constants.entityType.AD_GROUP, $ctrl.resolve.adGroupId, {
                adGroupId: $ctrl.resolve.adGroupId,
                destinationCampaignId: $ctrl.destinationCampaignId
            }).then(function (data) {
                reloadCache($ctrl.destinationCampaignId, data);

                var destinationCampaign = zemNavigationNewService.getEntityById(
                    constants.entityType.CAMPAIGN, $ctrl.destinationCampaignId);
                zemCloneAdGroupService.openResultsModal($ctrl.adGroup, destinationCampaign, data);

                $ctrl.modalInstance.close(data);
            }, function (errors) {
                $ctrl.errors = errors;
            }).finally(function () {
                $ctrl.requestInProgress = false;
            });
        }

        function getDataStore () {
            var promise = zemNavigationNewService.getNavigationHierarchyPromise().then(function () {
                return getDataStoreItems();
            });

            return zemSelectDataStore.createInstance(promise);
        }

        function getDataStoreItems () {
            var campaigns = [];
            angular.forEach(zemNavigationNewService.getNavigationHierarchy().ids.campaigns, function (value) {
                if (!value.data.archived) {
                    campaigns.push({
                        id: value.id,
                        name: value.name,
                        h1: value.parent.name,
                        searchableName: value.parent.name + ' ' + value.name,
                    });
                }
            });
            return campaigns;
        }

        function onCampaignSelected (item) {
            $ctrl.destinationCampaignId = item ? item.id : null;
        }

        function reloadCache (destinationCampaignId, entity) {
            // FIXME: Legacy workaround - When navigation service will be completely removed
            // this should be done automatically by listening entity services
            zemNavigationService.addAdGroupToCache(destinationCampaignId, {
                id: entity.id,
                name: entity.name,
                status: entity.status,
                state: entity.state,
                active: entity.active,
            });
        }
    }
});
