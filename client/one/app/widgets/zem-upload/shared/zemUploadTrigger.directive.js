/* globals angular */
'use strict';

angular.module('one.widgets').directive('zemUploadTrigger', function ($uibModal, $rootScope, zemUploadService) { // eslint-disable-line max-len
    return {
        restrict: 'A',
        replace: true,
        scope: {},
        bindToController: {
            adGroup: '=zemUploadAdGroup',
            onSave: '=zemUploadOnSave',
        },
        controllerAs: 'ctrl',
        link: function (scope, element, attrs, ctrl) {
            element.on('click', function () {
                zemUploadService.openUploadModal(ctrl.adGroup, ctrl.onSave);
            });
        },
        controller: function () {},
    };
});
