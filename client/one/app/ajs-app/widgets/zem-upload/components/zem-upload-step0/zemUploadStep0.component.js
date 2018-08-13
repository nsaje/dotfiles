angular.module('one.widgets').directive('zemUploadStep0', function() {
    // eslint-disable-line max-len
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
        template: require('./zemUploadStep0.component.html'),
        controller: 'ZemUploadStep0Ctrl',
    };
});

angular.module('one.widgets').controller('ZemUploadStep0Ctrl', function() {
    var vm = this;
    vm.switchToSingleContentAdUpload = function() {
        vm.endpoint.createBatch(vm.defaultBatchName).then(function(result) {
            vm.singleUploadCallback({
                batchId: result.batchId,
                batchName: result.batchName,
                candidates: result.candidates,
                autoOpenEditForm: true,
            });
        });
    };

    vm.switchToCsvUpload = function() {
        vm.csvUploadCallback();
    };
});
