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
            showDisplayUpload: '=',
        },
        controllerAs: 'ctrl',
        template: require('./zemUploadStep1.component.html'),
        controller: 'ZemUploadStep1Ctrl',
    };
});

angular
    .module('one.widgets')
    .controller('ZemUploadStep1Ctrl', function(config, $scope, zemAuthStore) {
        var vm = this;
        vm.config = config;
        vm.hasPermission = zemAuthStore.hasPermission.bind(zemAuthStore);

        vm.formData = {
            batchName: vm.defaultBatchName,
        };
        vm.formErrors = null;
        vm.requestFailed = false;
        vm.requestInProgress = false;

        if (vm.showDisplayUpload) {
            vm.exampleFileName = vm.hasPermission(
                'zemauth.can_use_3rdparty_js_trackers'
            )
                ? 'Zemanta_Display_Ads_Template_1'
                : 'Zemanta_Display_Ads_Template';
        } else {
            vm.exampleFileName = vm.hasPermission(
                'zemauth.can_use_3rdparty_js_trackers'
            )
                ? 'Zemanta_Content_Ads_Template_1'
                : 'Zemanta_Content_Ads_Template';
        }

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
