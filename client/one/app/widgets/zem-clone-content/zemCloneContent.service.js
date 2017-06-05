angular.module('one.widgets').service('zemCloneContentService', function ($uibModal, zemCloneContentEndpoint, zemNavigationNewService) { //eslint-disable-line max-len

    this.openCloneModal = openCloneModal;
    this.openResultsModal = openResultsModal;
    this.clone = clone;

    function openCloneModal (adGroupId, selection) {
        var modal = $uibModal.open({
            component: 'zemCloneContentModal',
            backdrop: 'static',
            keyboard: false,
            resolve: {
                adGroup: zemNavigationNewService.getEntityById(constants.entityType.AD_GROUP, adGroupId),
                selection: selection
            }
        });

        return modal.result;
    }

    function clone (config) {
        return zemCloneContentEndpoint.clone(config);
    }

    function openResultsModal (destinationBatch) {
        var modal = $uibModal.open({
            component: 'zemCloneContentSuccessfulModal',
            backdrop: 'static',
            keyboard: false,
            resolve: {
                destinationBatch: destinationBatch
            }
        });

        return modal.result;
    }
});
