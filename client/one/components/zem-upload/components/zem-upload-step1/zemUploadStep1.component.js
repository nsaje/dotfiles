/* globals angular, moment */
'use strict';

angular.module('one.legacy').directive('zemUploadStep1', [function () { // eslint-disable-line max-len
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        bindToController: {
            endpoint: '=',
            callback: '&',
            close: '=',
            user: '=',
            defaultBatchName: '=',
        },
        controllerAs: 'ctrl',
        templateUrl: '/components/zem-upload/components/zem-upload-step1/zemUploadStep1.component.html',
        controller: 'ZemUploadStep1Ctrl',
    };
}]);

angular.module('one.legacy').controller('ZemUploadStep1Ctrl', ['config', function (config) {
    var vm = this;
    vm.config = config;

    vm.formData = {
        batchName: vm.defaultBatchName,
    };
    vm.formErrors = null;
    vm.requestFailed = false;
    vm.requestInProgress = false;

    vm.clearFormErrors = function (field) {
        if (!vm.formErrors) {
            return;
        }
        delete vm.formErrors[field];
    };

    vm.upload = function () {
        vm.requestFailed = false;
        vm.requestInProgress = true;
        vm.endpoint.upload(vm.formData).then(
            function (result) {
                vm.callback({
                    batchId: result.batchId,
                    batchName: result.batchName,
                    candidates: result.candidates,
                });
            },
            function (data) {
                vm.requestFailed = true;
                vm.formErrors = data.errors;
            }
        ).finally(function () {
            vm.requestInProgress = false;
        });
    };
}]);
