/* globals angular */
'use strict';

angular.module('one.legacy').directive('zemUploadTrigger', function ($uibModal, $rootScope, zemUploadTriggerService) { // eslint-disable-line max-len
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
                zemUploadTriggerService.openUploadModal(ctrl.adGroup, ctrl.onSave);
            });
        },
        controller: function () {},
    };
});
