/* globals oneApp */
'use strict';

oneApp.directive('zemUpload', [function () { // eslint-disable-line max-len
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        templateUrl: '/components/zem-upload/zemUpload.component.html',
        bindToController: {
            adGroup: '=',
            onSave: '=',
            closeModal: '=',
        },
        controllerAs: 'ctrl',
        controller: 'ZemUploadCtrl',
    };
}]);

oneApp.controller('ZemUploadCtrl', ['zemUploadEndpointService', function (zemUploadEndpointService) {
    var vm = this;
    vm.api = zemUploadEndpointService.createEndpoint(vm.adGroup.id);
    vm.step = 1;

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
