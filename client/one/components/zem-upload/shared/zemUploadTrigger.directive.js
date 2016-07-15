/* globals oneApp */
'use strict';

oneApp.directive('zemUploadTrigger', ['$modal', '$rootScope', function ($modal, $rootScope) { // eslint-disable-line max-len
    return {
        restrict: 'A',
        replace: true,
        scope: {},
        bindToController: {
            adGroup: '=zemUploadAdGroup',
            onSave: '=zemUploadOnSave',
            user: '=zemUploadUser',
        },
        controllerAs: 'ctrl',
        link: function (scope, element, attrs, ctrl) {
            element.on('click', function () {
                var modalScope = $rootScope.$new();
                modalScope.adGroup = ctrl.adGroup;
                modalScope.onSave = ctrl.onSave;
                modalScope.user = ctrl.user;

                $modal.open({
                    template: '<zem-upload data-ad-group="adGroup" data-on-save="onSave" data-close-modal="closeModal" data-user="user"></zem-upload>',
                    controller: ['$scope', '$modalInstance', function ($scope, $modalInstance) {
                        $scope.closeModal = $modalInstance.close;
                    }],
                    windowClass: 'modal-zem-upload',
                    scope: modalScope,
                });
            });
        },
        controller: [function () {}],
    };
}]);
