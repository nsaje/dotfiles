angular.module('one.widgets').service('zemCloneAdGroupService', function ($uibModal, zemCloneAdGroupEndpoint, zemNavigationNewService) { //eslint-disable-line max-len

    this.openCloneModal = openCloneModal;
    this.clone = clone;

    function openCloneModal (campaignId, adGroupId) {
        var modal = $uibModal.open({
            component: 'zemCloneAdGroupModal',
            backdrop: 'static',
            keyboard: false,
            resolve: {
                campaign: zemNavigationNewService.getEntityById(constants.entityType.CAMPAIGN, campaignId),
                adGroup: zemNavigationNewService.getEntityById(constants.entityType.AD_GROUP, adGroupId)
            }
        });

        return modal.result;
    }

    function clone (config) {
        return zemCloneAdGroupEndpoint.clone(config);
    }
});
