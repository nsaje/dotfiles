angular.module('one.services').service('zemModalsService', function ($uibModal) { //eslint-disable-line max-len

    this.openConfirmModal = openConfirmModal;

    function openConfirmModal (text) {
        var modal = $uibModal.open({
            component: 'zemConfirmModal',
            backdrop: 'static',
            keyboard: false,
            resolve: {
                text: {value: text},
            }
        });

        return modal.result;
    }
});
