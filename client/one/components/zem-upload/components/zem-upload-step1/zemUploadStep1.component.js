/* globals oneApp, moment */
'use strict';

oneApp.directive('zemUploadStep1', [function () { // eslint-disable-line max-len
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        bindToController: {
            endpoint: '=',
            callback: '&',
            close: '=',
        },
        controllerAs: 'ctrl',
        templateUrl: '/components/zem-upload/components/zem-upload-step1/zemUploadStep1.component.html',
        controller: 'ZemUploadStep1Ctrl',
    };
}]);

oneApp.controller('ZemUploadStep1Ctrl', ['config', function (config) {
    var vm = this;
    vm.config = config;

    vm.formData = {
        batchName: moment().utc().add(
            vm.user ? vm.user.timezoneOffset : 0, 'seconds').format('M/D/YYYY h:mm A'),
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
