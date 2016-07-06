/* globals $, oneApp, constants, options, defaults, angular, moment */
oneApp.controller('UploadAdsModalCtrl', ['$interval', '$scope',  '$state', '$modalInstance', '$window', 'api', function ($interval, $scope, $state, $modalInstance, $window, api) { // eslint-disable-line max-len
    $scope.MAX_URL_LENGTH = 936;
    $scope.MAX_TITLE_LENGTH = 90;
    $scope.MAX_DESCRIPTION_LENGTH = 140;
    $scope.MAX_DISPLAY_URL_LENGTH = 25;
    $scope.MAX_BRAND_NAME_LENGTH = 25;
    $scope.MAX_CALL_TO_ACTION_LENGTH = 25;
    $scope.MAX_LABEL_LENGTH = 100;

    $scope.imageCrops = options.imageCrops;
    $scope.callToActionOptions = defaults.callToAction;
    $scope.candidateStatuses = constants.contentAdCandidateStatus;
    $scope.editFormScrollApi = {};

    var reset = function () {
        $scope.step = 1;
        $scope.candidates = [];
        $scope.selectedCandidate = null;
        $scope.batchNameEdit = false;
        $scope.uploadFormData = {};
        $scope.uploadFormData.batchName = moment().utc().add(
            $scope.user ? $scope.user.timezoneOffset : 0, 'seconds').format('M/D/YYYY h:mm A');
        $scope.anyCandidateHasErrors = false;
        $scope.batchId = null;
        $scope.numSuccessful = null;
        $scope.saveErrors = null;
        $scope.uploadFormErrors = null;
        $scope.stopPolling();
    };

    $scope.partials = [
        '/partials/upload_ads_modal_step1.html',
        '/partials/upload_ads_modal_step2.html',
        '/partials/upload_ads_modal_step3.html',
    ];

    $scope.startPolling = function () {
        if ($scope.pollInterval !== null) {
            return;
        }

        $scope.pollInterval = $interval(function () {
            var waitingCandidates = getWaitingCandidateIds();
            if (!waitingCandidates.length) {
                $scope.stopPolling();
                return;
            }
            api.upload.checkStatus($state.params.id, $scope.batchId, waitingCandidates).then(
                function (data) {
                    updateCandidates(data.candidates);
                }
            );
        }, 2500);
    };

    $scope.stopPolling = function () {
        if ($scope.pollInterval !== null) {
            $interval.cancel($scope.pollInterval);
            $scope.pollInterval = null;
        }
    };

    var updateCandidates = function (updatedCandidates) {
        angular.forEach(updatedCandidates, function (updatedCandidate) {
            var index = $.map($scope.candidates, function (candidate, ix) {
                if (candidate.id === updatedCandidate.id) {
                    return ix;
                }
            })[0];

            $scope.candidates.splice(index, 1, updatedCandidate);
        });
    };

    var getWaitingCandidateIds = function () {
        var ret = $scope.candidates.filter(function (candidate) {
            if ($scope.getStatus(candidate) === constants.contentAdCandidateStatus.LOADING) {
                return true;
            }
            return false;
        }).map(function (candidate) {
            return candidate.id;
        });
        return ret;
    };

    $scope.toggleBatchNameEdit = function () {
        $scope.batchNameEdit = !$scope.batchNameEdit;
    };

    $scope.disableBatchNameEdit = function () {
        $scope.batchNameEdit = false;
    };

    $scope.restart = function () {
        $scope.step = 1;
    };

    $scope.close = function () {
        $modalInstance.close();
    };

    $scope.openEditForm = function (candidate) {
        $scope.updateRequestInProgress = false;
        $scope.updateRequestFailed = false;
        $scope.selectedCandidate = angular.copy(candidate);
        $scope.selectedCandidate.defaults = {};
        $scope.selectedCandidate.useTrackers = !!$scope.selectedCandidate.primaryTrackerUrl ||
            !!$scope.selectedCandidate.secondaryTrackerUrl;
        $scope.selectedCandidate.useSecondaryTracker = !!$scope.selectedCandidate.secondaryTrackerUrl;

        if ($scope.editFormScrollApi.scroll) {
            $scope.editFormScrollApi.scroll();
        }
    };

    $scope.closeEditForm = function () {
        $scope.selectedCandidate = null;
    };

    $scope.isSaveDisabled = function () {
        return $scope.anyCandidateHasErrors || !$scope.candidates.length ||
            getWaitingCandidateIds().length || $scope.saveRequestInProgress;
    };

    var findCandidate = function (candidateId) {
        for (var i = 0; i < $scope.candidates.length; i++) {
            if ($scope.candidates[i].id === candidateId) {
                return $scope.candidates[i];
            }
        }
    };

    $scope.removeCandidate = function (selectedCandidate, event) {
        event.stopPropagation();  // the whole row has ng-click registered

        var candidate = findCandidate(selectedCandidate.id);
        candidate.removeRequestInProgress = true;
        candidate.removeRequestFailed = false;

        api.upload.removeCandidate(
            candidate.id,
            $state.params.id,
            $scope.batchId
        ).then(
            function () {
                $scope.candidates = $scope.candidates.filter(function (el) {
                    return candidate.id !== el.id;
                });

                if ($scope.selectedCandidate && ($scope.selectedCandidate.id === candidate.id)) {
                    $scope.closeEditForm();
                }
            },
            function () {
                candidate.removeRequestFailed = true;
            }
        ).finally(function () {
            candidate.removeRequestInProgress = false;
        });
    };

    $scope.addSecondaryTracker = function (candidate) {
        candidate.useSecondaryTracker = true;
    };

    $scope.removeSecondaryTracker = function (candidate) {
        candidate.useSecondaryTracker = false;
        candidate.secondaryTrackerUrl = null;
        $scope.clearSelectedCandidateErrors('secondaryTrackerUrl');
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

    $scope.switchToFileUpload = function () {
        reset();
    };

    $scope.switchToContentAdPicker = function () {
        $scope.step = 2;
    };

    $scope.switchToSuccessScreen = function () {
        $scope.step = 3;
    };

    $scope.getStatus = function (candidate) {
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

    $scope.save = function () {
        $scope.saveRequestFailed = false;
        $scope.saveRequestInProgress = true;
        api.upload.save($state.params.id, $scope.batchId, $scope.uploadFormData.batchName).then(
            function (data) {
                $scope.numSuccessful = data.numSuccessful;
                $scope.switchToSuccessScreen();
            },
            function (errors) {
                $scope.saveRequestFailed = true;
                $scope.saveErrors = errors;
            }
        ).finally(function () {
            $scope.saveRequestInProgress = false;
        });
    };

    $scope.clearSelectedCandidateErrors = function (field) {
        if (!$scope.selectedCandidate || !$scope.selectedCandidate.errors) {
            return;
        }

        delete $scope.selectedCandidate.errors[field];
    };

    $scope.clearUploadFormErrors = function (field) {
        if (!$scope.uploadFormErrors) {
            return;
        }

        delete $scope.uploadFormErrors[field];
    };

    $scope.clearBatchNameErrors = function () {
        if (!$scope.saveErrors) {
            return;
        }

        delete $scope.saveErrors.batchName;
    };

    $scope.getSaveErrorMsg = function () {
        if ($scope.saveRequestInProgress) {
            return;
        }

        if ($scope.anyCandidateHasErrors) {
            return 'You need to fix all errors before you can upload batch.';
        }

        if ($scope.saveErrors && $scope.saveErrors.batchName) {
            return $scope.saveErrors.batchName[0];
        }

        if ($scope.saveRequestFailed) {
            return 'Oops. Something went wrong. Please try again.';
        }
    };

    $scope.getContentErrorsMsg = function (candidate) {
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

    $scope.getImageErrorsMsg = function (candidate) {
        if (!candidate.errors || !candidate.errors.imageUrl) {
            return '';
        }

        var errs = candidate.errors.imageUrl;
        if (errs.length < 2) {
            return errs[0] || '';
        }

        return errs.length + ' image errors';
    };

    $scope.upload = function () {
        var uploadFormData = {
            file: $scope.uploadFormData.file,
            batchName: $scope.uploadFormData.batchName,
        };

        $scope.uploadRequestInProgress = true;
        api.upload.upload(
            $state.params.id, uploadFormData
        ).then(
            function (result) {
                $scope.candidates = result.candidates;
                $scope.batchId = result.batchId;
                $scope.switchToContentAdPicker();
                $scope.startPolling();
            },
            function (data) {
                $scope.uploadRequestFailed = true;
                $scope.uploadFormErrors = data.errors;
            }
        ).finally(function () {
            $scope.uploadRequestInProgress = false;
        });
    };

    $scope.updateCandidate = function () {
        $scope.updateRequestInProgress = true;
        api.upload.updateCandidate(
            $scope.selectedCandidate,
            $state.params.id,
            $scope.batchId
        ).then(function (result) {
            updateCandidates(result.candidates);
            $scope.startPolling();
            $scope.closeEditForm();
        }, function () {
            $scope.updateRequestFailed = true;
        }).finally(function () {
            $scope.updateRequestInProgress = false;
        });
    };

    $scope.download = function () {
        var url = '/api/ad_groups/' + $state.params.id + '/contentads/upload/' + $scope.batchId +
                '/download/?batch_name=' + encodeURIComponent($scope.uploadFormData.batchName);
        $window.open(url, '_blank');
    };

    $scope.cancel = function () {
        if ($scope.batchId) {
            api.upload.cancel($state.params.id, $scope.batchId);
        }
        $scope.stopPolling();
        $modalInstance.close();
    };

    $scope.callToActionSelect2Config = {
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

    $scope.$watchCollection('candidates', function () {
        $scope.anyCandidateHasErrors = checkAllCandidateErrors($scope.candidates);
        $scope.anyCandidateWaiting = getWaitingCandidateIds().length > 0;
    });

    $scope.$on('$destroy', function () {
        $scope.stopPolling();
    });

    reset();
}]);
