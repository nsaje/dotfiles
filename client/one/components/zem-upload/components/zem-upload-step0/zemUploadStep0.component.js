/* globals oneApp */
'use strict';

oneApp.directive('zemUploadStep0', [function () { // eslint-disable-line max-len
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        bindToController: {
            endpoint: '=',
            defaultBatchName: '=',
            singleUploadCallback: '&singleCallback',
            csvUploadCallback: '&csvCallback',
            close: '=',
        },
        controllerAs: 'ctrl',
        templateUrl: '/components/zem-upload/components/zem-upload-step0/zemUploadStep0.component.html',
        controller: 'ZemUploadStep0Ctrl',
    };
}]);

oneApp.controller('ZemUploadStep0Ctrl', [function () {
    var vm = this;
    vm.switchToSingleContentAdUpload = function () {
        vm.endpoint.createBatch(vm.defaultBatchName).then(
            function (result) {
                vm.singleUploadCallback({
                    batchId: result.batchId,
                    batchName: result.batchName,
                    candidates: [],
                });
            });
    };

    vm.switchToCsvUpload = function () {
        vm.csvUploadCallback();
    };
}]);
