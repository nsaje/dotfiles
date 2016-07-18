/* globals oneApp, constants, defaults, options, angular, $ */
'use strict';

oneApp.directive('zemUploadStep2', ['$window', function ($window) { // eslint-disable-line max-len
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        bindToController: {
            endpoint: '=',
            callback: '&',
            adGroup: '=',
            batchId: '=',
            batchName: '=',
            candidates: '=',
            onSave: '=',
            closeModal: '=close',
        },
        controllerAs: 'ctrl',
        templateUrl: '/components/zem-upload/components/zem-upload-step2/zemUploadStep2.component.html',
        link: function (scope, element, attrs, ctrl) {
            var batchNameInput = element.find('#batch-name-input');
            batchNameInput.on('click', function (event) {
                event.stopPropagation();
            });

            element.on('click', function () {
                ctrl.disableBatchNameEdit();
            });

            ctrl.focusBatchNameEdit = function () {
                batchNameInput[0].focus();
                batchNameInput[0].setSelectionRange(0, batchNameInput[0].value.length);
            };
        },
        controller: 'ZemUploadStep2Ctrl',
    };
}]);

oneApp.controller('ZemUploadStep2Ctrl', ['$scope', 'config', '$interval', '$window', '$scope', function ($scope, config, $interval, $window) {
    var vm = this;
    vm.config = config;

    vm.formData = {
        batchName: vm.batchName,
    };
    vm.batchNameEdit = false;
    vm.numSuccessful = null;
    vm.saveErrors = null;
    vm.editFormApi = {};

    vm.pollInterval = null;
    vm.startPolling = function () {
        if (vm.pollInterval !== null) {
            return;
        }

        vm.pollInterval = $interval(function () {
            var waitingCandidates = getWaitingCandidateIds();
            if (!waitingCandidates.length) {
                vm.stopPolling();
                return;
            }
            vm.endpoint.checkStatus(vm.batchId, waitingCandidates).then(
                function (data) {
                    updateCandidates(data.candidates);
                }
            );
        }, 2500);
    };

    vm.stopPolling = function () {
        if (vm.pollInterval !== null) {
            $interval.cancel(vm.pollInterval);
            vm.pollInterval = null;
        }
    };

    var updateCandidates = function (updatedCandidates) {
        angular.forEach(updatedCandidates, function (updatedCandidate) {
            var index = $.map(vm.candidates, function (candidate, ix) {
                if (candidate.id === updatedCandidate.id) {
                    return ix;
                }
            })[0];

            vm.candidates.splice(index, 1, updatedCandidate);
        });
    };

    var getWaitingCandidateIds = function () {
        var ret = vm.candidates.filter(function (candidate) {
            if (vm.getStatus(candidate) === constants.contentAdCandidateStatus.LOADING) {
                return true;
            }
            return false;
        }).map(function (candidate) {
            return candidate.id;
        });
        return ret;
    };

    vm.toggleBatchNameEdit = function ($event) {
        $event.stopPropagation();
        vm.batchNameEdit = !vm.batchNameEdit;
        if (vm.batchNameEdit) {
            vm.focusBatchNameEdit();
        }
    };

    vm.disableBatchNameEdit = function () {
        vm.batchNameEdit = false;
    };

    vm.isLoading = function () {
        return getWaitingCandidateIds().length ||
            vm.editFormApi.requestInProgress ||
            vm.saveRequestInProgress;
    };

    vm.isSaveDisabled = function () {
        return vm.isLoading() ||
            !vm.candidates.length ||
            checkAllCandidateErrors();
    };

    var findCandidate = function (candidateId) {
        for (var i = 0; i < vm.candidates.length; i++) {
            if (vm.candidates[i].id === candidateId) {
                return vm.candidates[i];
            }
        }
    };

    vm.removeCandidate = function (candidate, event) {
        event.stopPropagation();  // the whole row has ng-click registered

        candidate.removeRequestInProgress = true;
        candidate.removeRequestFailed = false;

        if (vm.editFormApi && vm.editFormApi.selectedId === candidate.id) {
            vm.editFormApi.close();
        }

        vm.endpoint.removeCandidate(
            candidate.id,
            vm.batchId
        ).then(
            function () {
                vm.candidates = vm.candidates.filter(function (el) {
                    return candidate.id !== el.id;
                });
            },
            function () {
                candidate.removeRequestFailed = true;
            }
        ).finally(function () {
            candidate.removeRequestInProgress = false;
        });
    };

    var hasErrors = function (candidate) {
        for (var key in candidate.errors) {
            if (candidate.errors.hasOwnProperty(key) && candidate.errors[key]) {
                return true;
            }
        }

        return false;
    };

    var checkAllCandidateErrors = function () {
        if (!vm.candidates) {
            return false;
        }

        for (var i = 0; i < vm.candidates.length; i++) {
            if (hasErrors(vm.candidates[i])) {
                return true;
            }
        }

        return false;
    };

    vm.getStatus = function (candidate) {
        if (candidate.imageStatus === constants.asyncUploadJobStatus.PENDING_START ||
            candidate.imageStatus === constants.asyncUploadJobStatus.WAITING_RESPONSE ||
            candidate.urlStatus === constants.asyncUploadJobStatus.PENDING_START ||
            candidate.urlStatus === constants.asyncUploadJobStatus.WAITING_RESPONSE) {
            return constants.contentAdCandidateStatus.LOADING;
        }

        if (hasErrors(candidate)) {
            return constants.contentAdCandidateStatus.ERRORS;
        }

        return constants.contentAdCandidateStatus.OK;
    };

    vm.updateCandidateCallback = function (candidates) {
        updateCandidates(candidates);
        vm.startPolling();
    };

    var executeSaveCall = function () {
        if (vm.isSaveDisabled()) {
            return;
        }

        vm.saveRequestFailed = false;
        vm.saveRequestInProgress = true;

        vm.endpoint.save(vm.batchId, vm.formData.batchName).then(
            function (data) {
                if (vm.onSave) {
                    vm.onSave();
                }
                vm.callback({
                    numSuccessful: data.numSuccessful,
                });
            },
            function (errors) {
                vm.saveRequestFailed = true;
                vm.saveErrors = errors;
            }
        ).finally(function () {
            vm.saveRequestInProgress = false;
        });
    };

    vm.save = function () {
        if (vm.editFormApi.selectedId) {
            vm.editFormApi.update().then(executeSaveCall);
        } else {
            executeSaveCall();
        }
    };

    vm.clearBatchNameErrors = function () {
        if (!vm.saveErrors) {
            return;
        }

        delete vm.saveErrors.batchName;
    };

    vm.getSaveErrorMsg = function () {
        if (vm.saveRequestInProgress) {
            return;
        }

        if (checkAllCandidateErrors()) {
            return 'You need to fix all errors before you can upload batch.';
        }

        if (vm.saveErrors && vm.saveErrors.batchName) {
            return vm.saveErrors.batchName[0];
        }

        if (vm.saveRequestFailed) {
            return 'Oops. Something went wrong. Please try again.';
        }
    };

    vm.getContentErrorsMsg = function (candidate) {
        if (!candidate.errors) {
            return '';
        }

        var errs = [];
        angular.forEach(candidate.errors, function (error, key) {
            if (key !== 'imageUrl') {
                Array.prototype.push.apply(errs, error);
            }
        });

        if (errs.length < 2) {
            return errs[0] || '';
        }

        return errs.length + ' content errors';
    };

    vm.getImageErrorsMsg = function (candidate) {
        if (!candidate.errors || !candidate.errors.imageUrl) {
            return '';
        }

        var errs = candidate.errors.imageUrl;
        if (errs.length < 2) {
            return errs[0] || '';
        }

        return errs.length + ' image errors';
    };

    vm.download = function () {
        var url = '/api/ad_groups/' + vm.adGroup.id + '/contentads/upload/' + vm.batchId +
                '/download/?batch_name=' + encodeURIComponent(vm.formData.batchName);
        $window.open(url, '_blank');
    };

    vm.cancel = function () {
        if (vm.batchId) {
            vm.endpoint.cancel(vm.batchId);
        }
        vm.stopPolling();
        vm.closeModal();
    };

    $scope.$on('$destroy', function () {
        vm.stopPolling();
    });

    vm.startPolling();
}]);
