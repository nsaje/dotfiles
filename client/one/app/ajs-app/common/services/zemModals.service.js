angular.module('one.services').service('zemModalsService', function($uibModal) {
    //eslint-disable-line max-len

    this.openConfirmModal = openConfirmModal;

    function openConfirmModal(text, title) {
        var modal = $uibModal.open({
            component: 'zemConfirmModal',
            backdrop: 'static',
            keyboard: false,
            resolve: {
                params: {
                    text: text,
                    title: title,
                },
            },
        });

        return modal.result;
    }
});
