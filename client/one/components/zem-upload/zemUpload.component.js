/* globals angular, moment */
'use strict';

angular.module('one.legacy').directive('zemUpload', [function () { // eslint-disable-line max-len
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        templateUrl: '/components/zem-upload/zemUpload.component.html',
        bindToController: {
            adGroup: '=',
            onSave: '=',
            closeModal: '=',
            user: '=',
            hasPermission: '=',
            isPermissionInternal: '=',
        },
        controllerAs: 'ctrl',
        controller: 'ZemUploadCtrl',
    };
}]);

angular.module('one.legacy').controller('ZemUploadCtrl', ['zemUploadEndpointService', function (zemUploadEndpointService) {
    var vm = this;
    vm.endpoint = zemUploadEndpointService.createEndpoint(vm.adGroup.id);
    vm.defaultBatchName = moment().utc().add(vm.user ? vm.user.timezoneOffset : 0, 'seconds').format('M/D/YYYY h:mm A');
    vm.step = 1;

    if (vm.hasPermission('zemauth.can_use_single_ad_upload')) {
        vm.step = 0;
    }

    vm.switchToFileUpload = function () {
        vm.step = 1;
    };

    vm.switchToContentAdPicker = function (batchId, batchName, candidates) {
        vm.batchId = batchId;
        vm.batchName = batchName;
        vm.candidates = candidates;
        vm.step = 2;
    };

    vm.switchToSuccessScreen = function (numSuccessful) {
        vm.numSuccessful = numSuccessful;
        vm.step = 3;
    };
}]);
