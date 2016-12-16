/* globals constants, defaults, options, angular, $ */
'use strict';

angular.module('one.legacy').directive('zemUploadStep2', function ($window) { // eslint-disable-line max-len
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        bindToController: {
            endpoint: '=',
            callback: '&',
            adGroupId: '=',
            batchId: '=',
            batchName: '=',
            candidates: '=',
            closeModal: '=close',
            autoOpenEditForm: '=',
            isEdit: '=',
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
});

angular.module('one.legacy').controller('ZemUploadStep2Ctrl', function ($scope, config, $interval, $window, $timeout) {
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
                    updateCandidatesStatuses(data.candidates);
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

    function updateCandidatesStatuses (updatedCandidates) {
        angular.forEach(updatedCandidates, function (updatedCandidate) {
            var candidate = vm.candidates.filter(function (candidate) {
                if (candidate.id === updatedCandidate.id) return true;
            })[0];

            if (updatedCandidate.imageStatus !== constants.asyncUploadJobStatus.PENDING_START) {
                candidate.imageStatus = updatedCandidate.imageStatus;
                if (updatedCandidate.errors.hasOwnProperty('imageUrl')) {
                    candidate.errors.imageUrl = updatedCandidate.errors.imageUrl;
                }
                if (updatedCandidate.hasOwnProperty('hostedImageUrl')) {
                    candidate.hostedImageUrl = updatedCandidate.hostedImageUrl;
                }
            }

            if (updatedCandidate.urlStatus !== constants.asyncUploadJobStatus.PENDING_START) {
                candidate.urlStatus = updatedCandidate.urlStatus;
                if (updatedCandidate.errors.hasOwnProperty('url')) {
                    candidate.errors.url = updatedCandidate.errors.url;
                }
            }
        });
    }

    function refreshCandidates (updatedCandidates, fields) {
        // fields parameter can be used to only selectively update fields and their error messages
        // If not specified, it updates all fields.
        // Example: use as default button in edit form
        angular.forEach(updatedCandidates, function (updatedCandidate) {
            var candidate = vm.candidates.filter(function (candidate) {
                if (candidate.id === updatedCandidate.id) return true;
            })[0];

            Object.keys(updatedCandidate).forEach(function (field) {
                if (field === 'errors') return;
                if (fields && fields.length && fields.indexOf(field) < 0) return;
                candidate[field] = updatedCandidate[field];
            });

            if (!fields || !fields.length) {
                candidate.errors = updatedCandidate.errors;
                return;
            }

            fields.forEach(function (field) {
                delete candidate.errors[field];
                if (updatedCandidate.errors[field]) candidate.errors[field] = updatedCandidate.errors[field];
            });
        });
    }

    function getWaitingCandidateIds () {
        var ret = vm.candidates.filter(function (candidate) {
            if (vm.getStatus(candidate) === constants.contentAdCandidateStatus.LOADING) {
                return true;
            }
            return false;
        }).map(function (candidate) {
            return candidate.id;
        });
        return ret;
    }

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

    vm.addCandidate = function () {
        vm.addCandidateRequestInProgress = true;
        vm.addCandidateRequestFailed = false;

        vm.endpoint.addCandidate(
            vm.batchId
        ).then(
            function (data) {
                vm.candidates.push(data.candidate);
                vm.editFormApi.open(data.candidate);
            },
            function () {
                vm.addCandidateRequestFailed = true;
            }
        ).finally(function () {
            vm.addCandidateRequestInProgress = false;
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
        if (candidate.imageStatus === constants.asyncUploadJobStatus.PENDING_START &&
            candidate.urlStatus === constants.asyncUploadJobStatus.PENDING_START) {
            // newly added candidate
            return null;
        }

        if (candidate.imageStatus === constants.asyncUploadJobStatus.WAITING_RESPONSE ||
            candidate.urlStatus === constants.asyncUploadJobStatus.WAITING_RESPONSE) {
            return constants.contentAdCandidateStatus.LOADING;
        }

        if (hasErrors(candidate)) {
            return constants.contentAdCandidateStatus.ERRORS;
        }

        if (candidate.imageStatus === constants.asyncUploadJobStatus.PENDING_START ||
            candidate.urlStatus === constants.asyncUploadJobStatus.PENDING_START) {
            // important to check this after checking for errors
            return null;
        }

        return constants.contentAdCandidateStatus.OK;
    };

    vm.updateCandidateCallback = function (fields) {
        vm.endpoint.getCandidates(vm.batchId).then(function (result) {
            updateCandidatesStatuses(result.candidates);
            if (fields && fields.length) refreshCandidates(result.candidates, fields);
            vm.startPolling();
        });
    };

    vm.refreshCandidatesCallback = function () {
        return vm.endpoint.getCandidates(vm.batchId).then(function (result) {
            refreshCandidates(result.candidates);
            vm.startPolling();
        });
    };

    var executeSaveCall = function () {
        if (vm.isSaveDisabled()) {
            return;
        }

        vm.saveRequestFailed = false;
        vm.saveRequestInProgress = true;

        vm.endpoint.save(vm.batchId, vm.formData.batchName).then(
            function (data) {
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
            vm.editFormApi.close().then(executeSaveCall);
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
            return 'You need to fix all errors before you can upload this batch.';
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
        var url = '/api/ad_groups/' + vm.adGroupId + '/contentads/upload/' + vm.batchId +
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

    if (vm.autoOpenEditForm) {
        $timeout(function () { // wait until edit form is loaded
            vm.editFormApi.open(vm.candidates[0]);
        }, 0);
    }

    vm.startPolling();
});
