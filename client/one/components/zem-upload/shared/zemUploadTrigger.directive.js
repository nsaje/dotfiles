/* globals angular */
'use strict';

angular.module('one.legacy').directive('zemUploadTrigger', ['$uibModal', '$rootScope', function ($uibModal, $rootScope) { // eslint-disable-line max-len
    return {
        restrict: 'A',
        replace: true,
        scope: {},
        bindToController: {
            adGroup: '=zemUploadAdGroup',
            onSave: '=zemUploadOnSave',
            user: '=zemUploadUser',
            hasPermission: '=zemHasPermission',
            isPermissionInternal: '=zemIsPermissionInternal',
        },
        controllerAs: 'ctrl',
        link: function (scope, element, attrs, ctrl) {
            element.on('click', function () {
                var modalScope = $rootScope.$new();
                modalScope.adGroup = ctrl.adGroup;
                modalScope.onSave = ctrl.onSave;
                modalScope.user = ctrl.user;
                modalScope.hasPermission = ctrl.hasPermission;
                modalScope.isPermissionInternal = ctrl.isPermissionInternal;

                $uibModal.open({
                    template: '<zem-upload data-ad-group="adGroup" data-on-save="onSave" data-close-modal="closeModal" data-user="user" data-has-permission="hasPermission" data-is-permission-internal="isPermissionInternal"></zem-upload>',
                    controller: ['$scope', function ($scope) {
                        $scope.closeModal = $scope.$close;
                    }],
                    windowClass: 'modal-zem-upload',
                    scope: modalScope,
                });
            });
        },
        controller: [function () {}],
    };
}]);
