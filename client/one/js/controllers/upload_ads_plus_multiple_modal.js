/* globals $, oneApp, constants, options, defaults, angular, moment */
oneApp.controller('UploadAdsPlusMultipleModalCtrl', ['$interval', '$scope',  '$state', '$modalInstance', 'api', function ($interval, $scope, $state, $modalInstance, api) { // eslint-disable-line max-len
    $scope.imageCrops = options.imageCrops;
    $scope.callToActionOptions = defaults.callToAction;
    $scope.candidateStatuses = constants.contentAdCandidateStatus;

    $scope.partials = [
        '/partials/upload_ads_plus_multiple_modal_step1.html',
        '/partials/upload_ads_plus_multiple_modal_step2.html',
        '/partials/upload_ads_plus_multiple_modal_step3.html',
    ];

    $scope.step = 1;
    $scope.selectedCandidate = null;
    $scope.batchNameEdit = false;
    $scope.batchName = moment().format('M/D/YYYY h:mm A');
    $scope.fileInput = {};

    var pollInterval;
    var startPolling = function (batchId) {
        if (angular.isDefined(pollInterval)) {
            return;
        }

        pollInterval = $interval(function () {
            var waitingCandidates = getWaitingCandidateIds();
            if (!waitingCandidates.length) {
                stopPolling();
                return;
            }
            api.uploadPlus.checkStatus($state.params.id, batchId, waitingCandidates).then(
                function (data) {
                    updateCandidates(data.candidates);
                }
            );
        }, 1000);
    };

    var stopPolling = function () {
        if (angular.isDefined(pollInterval)) {
            $interval.cancel(pollInterval);
            pollInterval = undefined;
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
        $scope.selectedCandidate = angular.copy(candidate);
        $scope.selectedCandidate.defaults = {};
        $scope.selectedCandidate.useTrackers = !!$scope.selectedCandidate.primaryTrackerUrl ||
            !!$scope.selectedCandidate.secondaryTrackerUrl;
        $scope.selectedCandidate.useSecondaryTracker = !!$scope.selectedCandidate.secondaryTrackerUrl;
    };

    $scope.closeEditForm = function () {
        $scope.selectedCandidate = null;
    };

    $scope.isUploadDisabled = function () {
        return $scope.anyErrors || !$scope.candidates.length || getWaitingCandidateIds().length;
    };

    $scope.removeCandidate = function (candidate) {
        api.uploadPlus.removeCandidate(
            candidate.id,
            $state.params.id,
            $scope.batchId
        ).then(function () {
            $scope.candidates = $scope.candidates.filter(function (el) {
                return candidate.id !== el.id;
            });

            if ($scope.selectedCandidate && ($scope.selectedCandidate.id === candidate.id)) {
                $scope.closeEditForm();
            }
        });
    };

    $scope.addSecondaryTracker = function (candidate) {
        candidate.useSecondaryTracker = true;
    };

    $scope.removeSecondaryTracker = function (candidate) {
        candidate.useSecondaryTracker = false;
        candidate.secondaryTrackerUrl = undefined;
        $scope.clearCandidateErrors('secondaryTrackerUrl');
    };

    var candidateHasErrors = function (candidate) {
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
            if (candidateHasErrors(candidates[i])) {
                return true;
            }
        }

        return false;
    };

    $scope.getStatus = function (candidate) {
        if (candidate.imageStatus === constants.asyncUploadJobStatus.PENDING_START ||
            candidate.imageStatus === constants.asyncUploadJobStatus.WAITING_RESPONSE ||
            candidate.urlStatus === constants.asyncUploadJobStatus.PENDING_START ||
            candidate.urlStatus === constants.asyncUploadJobStatus.WAITING_RESPONSE) {
            return constants.contentAdCandidateStatus.LOADING;
        }

        if (candidateHasErrors(candidate)) {
            return constants.contentAdCandidateStatus.ERRORS;
        }

        return constants.contentAdCandidateStatus.OK;
    };

    $scope.saveUpload = function () {
        api.uploadPlus.save($state.params.id, $scope.batchId, $scope.batchName).then(
            function (data) {
                $scope.numSuccessful = data.numSuccessful;
                $scope.step++;
            }
        );
    };

    $scope.clearCandidateErrors = function (field) {
        if (!$scope.selectedCandidate || !$scope.selectedCandidate.errors) {
            return;
        }

        delete $scope.selectedCandidate.errors[field];
    };

    $scope.getContentErrors = function (candidate) {
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

    $scope.getImageErrors = function (candidate) {
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
        if ($scope.uploadStatus === constants.uploadBatchStatus.IN_PROGRESS) {
            return;
        }

        var formData = {
            file: $scope.fileInput.file,
            batchName: $scope.batchName,
        };

        api.uploadPlus.uploadMultiple(
            $state.params.id, formData
        ).then(function (result) {
            $scope.step++;
            $scope.candidates = result.candidates;
            $scope.batchId = result.batchId;
            startPolling($scope.batchId);
        }, function (data) {
            $scope.errors = data.errors;
        });
    };

    $scope.updateCandidate = function () {
        api.uploadPlus.updateCandidate(
            $scope.selectedCandidate,
            $state.params.id,
            $scope.batchId
        ).then(function (result) {
            updateCandidates(result.candidates);
            startPolling($scope.batchId);
            $scope.closeEditForm();
        });
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
        $scope.anyErrors = checkAllCandidateErrors($scope.candidates);
    });

    $scope.$on('$destroy', function () {
        stopPolling();
    });
}]);
