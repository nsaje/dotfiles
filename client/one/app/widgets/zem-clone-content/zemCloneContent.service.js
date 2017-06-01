angular.module('one.widgets').service('zemCloneContentService', function ($uibModal, zemCloneContentEndpoint) { //eslint-disable-line max-len

    this.openCloneModal = openCloneModal;
    this.clone = clone;

    function openCloneModal (adGroupId, selection) {
        var modal = $uibModal.open({
            component: 'zemCloneContentModal',
            backdrop: 'static',
            keyboard: false,
            resolve: {
                adGroupId: adGroupId,
                selection: selection,
            }
        });

        return modal.result;
    }

    function clone (config) {
        return zemCloneContentEndpoint.clone(config);
    }
});
