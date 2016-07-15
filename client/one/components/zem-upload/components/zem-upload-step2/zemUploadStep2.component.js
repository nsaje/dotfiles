/* globals oneApp, constants, defaults, options, angular, $ */
'use strict';

oneApp.directive('zemUploadStep2', [function () { // eslint-disable-line max-len
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        bindToController: {
            api: '=',
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
        controller: 'ZemUploadStep2Ctrl',
    };
}]);

oneApp.controller('ZemUploadStep2Ctrl', ['$scope', 'config', '$interval', '$window', '$scope', function ($scope, config, $interval, $window) {
    var vm = this;
    vm.config = config;

    vm.MAX_URL_LENGTH = 936;
    vm.MAX_TITLE_LENGTH = 90;
    vm.MAX_DESCRIPTION_LENGTH = 140;
    vm.MAX_DISPLAY_URL_LENGTH = 25;
    vm.MAX_BRAND_NAME_LENGTH = 25;
    vm.MAX_CALL_TO_ACTION_LENGTH = 25;
    vm.MAX_LABEL_LENGTH = 100;

    vm.imageCrops = options.imageCrops;
    vm.callToActionOptions = defaults.callToAction;
    vm.candidateStatuses = constants.contentAdCandidateStatus;
    vm.editFormScrollApi = {};

    vm.formData = {
        batchName: vm.batchName,
    };
    vm.selectedCandidate = null;
    vm.batchNameEdit = false;
    vm.anyCandidateHasErrors = false;
    vm.numSuccessful = null;
    vm.saveErrors = null;

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
            vm.api.checkStatus(vm.batchId, waitingCandidates).then(
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

    vm.toggleBatchNameEdit = function () {
        vm.batchNameEdit = !vm.batchNameEdit;
    };

    vm.disableBatchNameEdit = function () {
        vm.batchNameEdit = false;
    };

    vm.openEditForm = function (candidate) {
        vm.updateRequestInProgress = false;
        vm.updateRequestFailed = false;
        vm.selectedCandidate = angular.copy(candidate);
        vm.selectedCandidate.defaults = {};
        vm.selectedCandidate.useTrackers = !!vm.selectedCandidate.primaryTrackerUrl ||
            !!vm.selectedCandidate.secondaryTrackerUrl;
        vm.selectedCandidate.useSecondaryTracker = !!vm.selectedCandidate.secondaryTrackerUrl;

        if (vm.editFormScrollApi.scroll) {
            vm.editFormScrollApi.scroll();
        }
    };

    vm.closeEditForm = function () {
        vm.selectedCandidate = null;
    };

    vm.isSaveDisabled = function () {
        return vm.anyCandidateHasErrors || !vm.candidates.length ||
            vm.anyCandidateWaiting || vm.saveRequestInProgress;
    };

    var findCandidate = function (candidateId) {
        for (var i = 0; i < vm.candidates.length; i++) {
            if (vm.candidates[i].id === candidateId) {
                return vm.candidates[i];
            }
        }
    };

    vm.removeCandidate = function (selectedCandidate, event) {
        event.stopPropagation();  // the whole row has ng-click registered

        var candidate = findCandidate(selectedCandidate.id);
        candidate.removeRequestInProgress = true;
        candidate.removeRequestFailed = false;

        vm.api.removeCandidate(
            candidate.id,
            vm.batchId
        ).then(
            function () {
                vm.candidates = vm.candidates.filter(function (el) {
                    return candidate.id !== el.id;
                });

                if (vm.selectedCandidate && (vm.selectedCandidate.id === candidate.id)) {
                    vm.closeEditForm();
                }
            },
            function () {
                candidate.removeRequestFailed = true;
            }
        ).finally(function () {
            candidate.removeRequestInProgress = false;
        });
    };

    vm.addSecondaryTracker = function (candidate) {
        candidate.useSecondaryTracker = true;
    };

    vm.removeSecondaryTracker = function (candidate) {
        candidate.useSecondaryTracker = false;
        candidate.secondaryTrackerUrl = null;
        vm.clearSelectedCandidateErrors('secondaryTrackerUrl');
    };

    var hasErrors = function (candidate) {
        for (var key in candidate.errors) {
            if (candidate.errors.hasOwnProperty(key) && candidate.errors[key]) {
                return true;
            }
        }

        return false;
    };

    var checkAllCandidateErrors = function (candidates) {
        if (!candidates) {
            return false;
        }

        for (var i = 0; i < candidates.length; i++) {
            if (hasErrors(candidates[i])) {
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

    vm.save = function () {
        vm.saveRequestFailed = false;
        vm.saveRequestInProgress = true;
        vm.api.save(vm.batchId, vm.formData.batchName).then(
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

    vm.clearSelectedCandidateErrors = function (field) {
        if (!vm.selectedCandidate || !vm.selectedCandidate.errors) {
            return;
        }

        delete vm.selectedCandidate.errors[field];
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

        if (vm.anyCandidateHasErrors) {
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

    vm.updateCandidate = function () {
        vm.updateRequestInProgress = true;
        vm.updateRequestFailed = false;
        vm.api.updateCandidate(
            vm.selectedCandidate,
            vm.batchId
        ).then(function (result) {
            updateCandidates(result.candidates);
            vm.startPolling();
            vm.closeEditForm();
        }, function () {
            vm.updateRequestFailed = true;
        }).finally(function () {
            vm.updateRequestInProgress = false;
        });
    };

    vm.download = function () {
        var url = '/api/ad_groups/' + vm.adGroup.id + '/contentads/upload/' + vm.batchId +
                '/download/?batch_name=' + encodeURIComponent(vm.formData.batchName);
        $window.open(url, '_blank');
    };

    vm.cancel = function () {
        if (vm.batchId) {
            vm.api.cancel(vm.batchId);
        }
        vm.stopPolling();
        vm.closeModal();
    };

    vm.callToActionSelect2Config = {
        dropdownCssClass: 'service-fee-select2',
        createSearchChoice: function (term, data) {
            if ($(data).filter(function () {
                return this.text.localeCompare(term) === 0;
            }).length === 0) {
                return {id: term, text: term};
            }
        },
        data: defaults.callToAction,
    };

    $scope.$watchCollection('ctrl.candidates', function () {
        vm.anyCandidateHasErrors = checkAllCandidateErrors(vm.candidates);
        vm.anyCandidateWaiting = getWaitingCandidateIds().length > 0;
    });

    $scope.$on('$destroy', function () {
        vm.stopPolling();
    });

    vm.startPolling();
}]);
