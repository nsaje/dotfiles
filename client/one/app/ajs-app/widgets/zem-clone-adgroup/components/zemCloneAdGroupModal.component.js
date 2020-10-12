require('./zemCloneAdGroupModal.component.less');
var commonHelpers = require('../../../../shared/helpers/common.helpers');

angular.module('one.widgets').component('zemCloneAdGroupModal', {
    bindings: {
        resolve: '<',
        modalInstance: '<',
    },
    template: require('./zemCloneAdGroupModal.component.html'),
    controller: function(
        $q,
        zemNavigationService,
        zemNavigationNewService,
        zemCloneAdGroupService,
        zemSelectDataStore,
        zemEntityService
    ) {
        // eslint-disable-line max-len
        var $ctrl = this;
        $ctrl.texts = {
            placeholder: 'Search campaign ...',
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
        $ctrl.destinationAdGroupName = null;
        $ctrl.cloneAds = true;

        $ctrl.errors = null;
        $ctrl.requestInProgress = false;

        $ctrl.$onInit = function() {
            var promise = zemNavigationNewService
                .getNavigationHierarchyPromise()
                .then(function() {
                    return $q.all({
                        campaign: zemNavigationNewService.getEntityById(
                            constants.entityType.CAMPAIGN,
                            $ctrl.resolve.campaignId
                        ),
                        adGroup: zemNavigationNewService.getEntityById(
                            constants.entityType.AD_GROUP,
                            $ctrl.resolve.adGroupId
                        ),
                    });
                })
                .then(function(entities) {
                    $ctrl.campaign = entities.campaign;
                    $ctrl.adGroup = entities.adGroup;
                    $ctrl.destinationAdGroupName =
                        $ctrl.adGroup.name + ' (Copy)';

                    return getDataStoreItems();
                });
            $ctrl.store = zemSelectDataStore.createInstance(promise);
        };

        function submit() {
            $ctrl.requestInProgress = true;

            zemEntityService
                .cloneEntity(
                    constants.entityType.AD_GROUP,
                    $ctrl.resolve.adGroupId,
                    {
                        adGroupId: $ctrl.resolve.adGroupId,
                        destinationCampaignId: $ctrl.destinationCampaignId,
                        destinationAdGroupName: $ctrl.destinationAdGroupName,
                        cloneAds: $ctrl.cloneAds,
                    }
                )
                .then(
                    function(data) {
                        if (commonHelpers.isDefined(data)) {
                            reloadCache(data);
                        }

                        zemNavigationNewService
                            .getEntityById(
                                constants.entityType.CAMPAIGN,
                                $ctrl.destinationCampaignId
                            )
                            .then(function(destinationCampaign) {
                                zemCloneAdGroupService.openResultsModal(
                                    $ctrl.adGroup,
                                    destinationCampaign,
                                    data
                                );
                            });

                        $ctrl.modalInstance.close();
                    },
                    function(errors) {
                        $ctrl.errors = errors;
                    }
                )
                .finally(function() {
                    $ctrl.requestInProgress = false;
                });
        }

        function getDataStoreItems() {
            var item,
                campaigns = [];
            angular.forEach(
                zemNavigationNewService.getNavigationHierarchy().ids.campaigns,
                function(value) {
                    if (value.data.archived) {
                        return;
                    }
                    item = {
                        id: value.id,
                        name: value.name,
                        h1: value.parent.name,
                        searchableName: value.parent.name + ' ' + value.name,
                    };
                    if (value.parent.id === $ctrl.campaign.parent.id) {
                        campaigns.push(item);
                    }
                }
            );
            return campaigns;
        }

        function onCampaignSelected(item) {
            $ctrl.destinationCampaignId = item ? item.id : null;
        }

        function reloadCache(entity) {
            // FIXME: Legacy workaround - When navigation service will be completely removed
            // this should be done automatically by listening entity services
            zemNavigationService.reloadAdGroup(entity.id);
        }
    },
});
