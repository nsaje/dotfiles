angular.module('one.widgets').directive('zemUploadStep2', function($timeout) {
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        bindToController: {
            endpoint: '=',
            callback: '&',
            batchId: '=',
            batchName: '=',
            candidates: '=',
            closeModal: '=close',
            autoOpenEditForm: '=',
            showVideoUpload: '=',
            showDisplayUpload: '=',
            isEdit: '=',
        },
        controllerAs: 'ctrl',
        template: require('./zemUploadStep2.component.html'),
        link: function(scope, element, attrs, ctrl) {
            var batchNameInput;
            $timeout(function() {
                batchNameInput = element.find('#batch-name-input');
                batchNameInput.on('click', function(event) {
                    event.stopPropagation();
                });
            }, 0);

            element.on('click', function() {
                ctrl.disableBatchNameEdit();
            });

            ctrl.focusBatchNameEdit = function() {
                batchNameInput[0].focus();
                batchNameInput[0].setSelectionRange(
                    0,
                    batchNameInput[0].value.length
                );
            };
        },
        controller: 'ZemUploadStep2Ctrl',
    };
});

angular
    .module('one.widgets')
    .controller('ZemUploadStep2Ctrl', function(
        $scope,
        config,
        $interval,
        $window,
        $timeout
    ) {
        var vm = this;
        vm.config = config;

        vm.formData = {
            batchName: vm.batchName,
        };
        vm.batchNameEdit = false;
        vm.numSuccessful = null;
        vm.saveErrors = null;

        vm.adPickerApi = {};
        vm.editFormApi = {};

        vm.toggleBatchNameEdit = function($event) {
            $event.stopPropagation();
            vm.batchNameEdit = !vm.batchNameEdit;
            if (vm.batchNameEdit) {
                setTimeout(vm.focusBatchNameEdit, 0);
            }
        };

        vm.disableBatchNameEdit = function() {
            vm.batchNameEdit = false;
        };

        function isAnyVideoAssetBeingProcessed() {
            for (var i = 0; i < vm.candidates.length; i++) {
                if (
                    vm.adPickerApi.isVideoAssetBeingProcessed(vm.candidates[i])
                ) {
                    return true;
                }
            }
            return false;
        }

        function areAnyVideoAssetProcessingErrorsPresent() {
            for (var i = 0; i < vm.candidates.length; i++) {
                if (
                    vm.adPickerApi.isVideoAssetProcessingErrorPresent(
                        vm.candidates[i]
                    )
                ) {
                    return true;
                }
            }
            return false;
        }

        vm.isLoading = function() {
            return (
                vm.adPickerApi.getWaitingCandidateIds().length ||
                isAnyVideoAssetBeingProcessed() ||
                vm.editFormApi.requestInProgress ||
                vm.saveRequestInProgress
            );
        };

        vm.isSaveDisabled = function() {
            return (
                vm.isLoading() ||
                isAnyVideoAssetBeingProcessed() ||
                !vm.candidates.length ||
                checkAllCandidateErrors()
            );
        };

        var checkAllCandidateErrors = function() {
            if (!vm.candidates) {
                return false;
            }

            for (var i = 0; i < vm.candidates.length; i++) {
                if (vm.adPickerApi.hasErrors(vm.candidates[i])) {
                    return true;
                }
            }

            if (areAnyVideoAssetProcessingErrorsPresent()) {
                return true;
            }

            return false;
        };

        var executeSaveCall = function() {
            if (vm.isSaveDisabled()) {
                return;
            }

            vm.saveRequestFailed = false;
            vm.saveRequestInProgress = true;

            vm.endpoint
                .save(vm.batchId, vm.formData.batchName)
                .then(
                    function(data) {
                        vm.callback({
                            numSuccessful: data.numSuccessful,
                        });
                    },
                    function(errors) {
                        vm.saveRequestFailed = true;
                        vm.saveErrors = errors;
                    }
                )
                .finally(function() {
                    vm.saveRequestInProgress = false;
                });
        };

        vm.save = function() {
            if (vm.editFormApi.selectedId) {
                vm.editFormApi.close().then(executeSaveCall);
            } else {
                executeSaveCall();
            }
        };

        vm.clearBatchNameErrors = function() {
            if (!vm.saveErrors) {
                return;
            }

            delete vm.saveErrors.batchName;
        };

        vm.getSaveErrorMsg = function() {
            if (vm.saveRequestInProgress) {
                return;
            }

            if (checkAllCandidateErrors()) {
                return 'You need to fix all errors before you can upload this batch.';
            }

            if (vm.saveErrors && vm.saveErrors.batchName) {
                return vm.saveErrors.batchName[0];
            }

            if (vm.saveRequestFailed) {
                return 'Oops. Something went wrong. Please try again.';
            }
        };

        vm.cancel = function() {
            if (vm.batchId) {
                vm.endpoint.cancel(vm.batchId);
            }
            vm.closeModal(false);
        };

        if (vm.autoOpenEditForm) {
            $timeout(function() {
                // wait until edit form is loaded
                vm.editFormApi.open(vm.candidates[0]);
            }, 0);
        }
    });
