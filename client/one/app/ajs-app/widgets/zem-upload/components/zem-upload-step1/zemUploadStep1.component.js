angular.module('one.widgets').directive('zemUploadStep1', function() {
    // eslint-disable-line max-len
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        bindToController: {
            endpoint: '=',
            callback: '&',
            close: '=',
            defaultBatchName: '=',
        },
        controllerAs: 'ctrl',
        template: require('./zemUploadStep1.component.html'),
        controller: 'ZemUploadStep1Ctrl',
    };
});

angular
    .module('one.widgets')
    .controller('ZemUploadStep1Ctrl', function(config, $scope) {
        var vm = this;
        vm.config = config;

        vm.formData = {
            batchName: vm.defaultBatchName,
        };
        vm.formErrors = null;
        vm.requestFailed = false;
        vm.requestInProgress = false;

        vm.clearFormErrors = function(field) {
            if (!vm.formErrors) {
                return;
            }
            delete vm.formErrors[field];
        };

        vm.fileUploadCallback = function(file) {
            vm.formData.file = file;
            $scope.$digest();
        };

        vm.upload = function() {
            vm.requestFailed = false;
            vm.requestInProgress = true;
            vm.endpoint
                .upload(vm.formData)
                .then(
                    function(result) {
                        vm.callback({
                            batchId: result.batchId,
                            batchName: result.batchName,
                            candidates: result.candidates,
                        });
                    },
                    function(data) {
                        vm.requestFailed = true;
                        vm.formErrors = data.errors;
                    }
                )
                .finally(function() {
                    vm.requestInProgress = false;
                });
        };
    });
