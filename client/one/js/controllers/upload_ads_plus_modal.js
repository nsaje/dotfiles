/* globals $,constants,oneApp,angular,defaults */
oneApp.controller('UploadAdsPlusModalCtrl', ['$scope', '$modalInstance', 'api', '$state', '$interval', function ($scope, $modalInstance, api, $state, $interval) { // eslint-disable-line max-len
    $scope.uploadBatchStatusConstants = constants.uploadBatchStatus;

    $scope.formData = {};
    // initialize to an empty value - just so that we avoid seeing "undefined"
    // for a moment before the defaults load
    $scope.formData.callToAction = '';

    $scope.count = null;
    $scope.batchSize = null;
    $scope.uploadStatus = null;
    $scope.errors = null;
    $scope.batchId = null;
    $scope.isCancelDisabled = false;
    $scope.numErrors = 0;
    $scope.errorReport = null;

    var pollInterval;
    var stopPolling = function () {
        if (angular.isDefined(pollInterval)) {
            $interval.cancel(pollInterval);
        }
        pollInterval = undefined;
    };

    var saveUpload = function () {
        api.uploadPlus.save($state.params.id, $scope.batchId).then(
            function (data) {
                $scope.numErrors = data.numErrors;
                $scope.errorReport = data.errorReport;
                $scope.uploadStatus = constants.uploadBatchStatus.DONE;
            },
            function () {
                $scope.uploadStatus = constants.uploadBatchStatus.FAILED;
            }
        );
    };

    var updateUploadStatus = function (candidates) {
        var count = 0;
        angular.forEach(candidates, function (status) {
            if (status.imageStatus !== constants.asyncUploadJobStatus.PENDING_START &&
                status.urlStatus !== constants.asyncUploadJobStatus.WAITING_RESPONSE &&
                status.urlStatus !== constants.asyncUploadJobStatus.PENDING_START &&
                status.urlStatus !== constants.asyncUploadJobStatus.WAITING_RESPONSE) {
                count += 1;
            }
        });
        $scope.count = count;

        if ($scope.count === $scope.batchSize) {
            $scope.isCancelDisabled = true;
            stopPolling();
            saveUpload();
        }
    };

    $scope.getProgressPercentage = function () {
        return $scope.batchSize ? $scope.count * 100 / $scope.batchSize : 0;
    };

    $scope.getErrorDescription = function () {
        if (!$scope.errors || !$scope.errors.details) {
            return '';
        }
        return $scope.errors.details.description;
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

    $scope.pollBatchStatus = function (batchId) {
        if ($scope.uploadStatus === constants.uploadBatchStatus.IN_PROGRESS) {
            pollInterval = $interval(function () {
                api.uploadPlus.checkStatus($state.params.id, batchId).then(
                    function (data) {
                        updateUploadStatus(data.candidates);
                    },
                    function () {
                        $scope.uploadStatus = constants.uploadBatchStatus.FAILED;
                    }
                );
            }, 1000);
        }
    };

    var replaceStart = /^https?:\/\//;
    var replaceEnd = /\/$/;
    function cleanDisplayUrl (data) {
        if (data.displayUrl === undefined) {
            return;
        }

        data.displayUrl = data.displayUrl.replace(replaceStart, '');
        data.displayUrl = data.displayUrl.replace(replaceEnd, '');
    }

    $scope.clearErrors = function (name) {
        if (!$scope.errors) {
            return;
        }
        delete $scope.errors[name];
    };

    $scope.upload = function () {
        if ($scope.uploadStatus === constants.uploadBatchStatus.IN_PROGRESS) {
            return;
        }

        cleanDisplayUrl($scope.formData);

        api.uploadPlus.uploadMultiple(
            $state.params.id, $scope.formData
        ).then(function (result) {
            $scope.uploadStatus = constants.uploadBatchStatus.IN_PROGRESS;
            $scope.batchSize = result.candidates.length;
            $scope.count = 0;
            $scope.batchId = result.batchId;

            $scope.pollBatchStatus(result.batchId);
        }, function (data) {
            $scope.errors = data.errors;
        });
    };

    $scope.init = function () {
        api.uploadPlus.getDefaults($state.params.id).then(
            function (data) {
                angular.extend($scope.formData, data.defaults);
                $scope.formData.batchName = '';
            });
    };

    $scope.$watch('formData.file', function (newValue) {
        if ($scope.formData.batchName !== '' || !newValue) {
            return;
        }
        $scope.formData.batchName = newValue.name;
    });

    $scope.cancel = function () {
        api.uploadPlus.cancel($state.params.id, $scope.batchId);
        $scope.uploadStatus = constants.uploadBatchStatus.CANCELLED;
        stopPolling();
    };

    $scope.viewUploadedAds = function () {
        $modalInstance.close();
    };

    $scope.$on('$destroy', function () {
        stopPolling();
    });

    $scope.init();
}]);
