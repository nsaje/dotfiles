angular.module('one.widgets').service('zemCloneAdGroupService', function ($uibModal, zemCloneAdGroupEndpoint) { //eslint-disable-line max-len

    this.openCloneModal = openCloneModal;
    this.clone = clone;

    function openCloneModal (campaignId, adGroup) {
        var modal = $uibModal.open({
            component: 'zemCloneAdGroupModal',
            backdrop: 'static',
            keyboard: false,
            resolve: {
                campaignId: campaignId,
                adGroup: adGroup,
            }
        });

        return modal.result;
    }

    function clone (config) {
        return zemCloneAdGroupEndpoint.clone(config);
    }
});
