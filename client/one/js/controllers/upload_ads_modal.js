/* globals $,constants,oneApp,angular,defaults */
oneApp.controller('UploadAdsModalCtrl', ['$scope', '$modalInstance', 'api', '$state', '$timeout', '$filter', function ($scope, $modalInstance, api, $state, $timeout, $filter) {
    $scope.uploadBatchStatusConstants = constants.uploadBatchStatus;

    $scope.formData = {};
    // initialize to an empty value - just so that we avoid seeing "undefined"
    // for a moment before the defaults load
    $scope.formData.callToAction = '';

    $scope.steps = [
        'Uploading', 'Processing imported file', 'Inserting content ads', 'Propagating content ads to media sources',
    ];

    function resetUploadStatus () {
        $scope.step = null;
        $scope.count = null;
        $scope.batchSize = null;
        $scope.uploadStatus = null;
        $scope.errors = null;
        $scope.batchId = null;
        $scope.cancelErrors = null;
    }

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
            $timeout(function () {
                api.adGroupAdsPlusUpload.checkStatus($state.params.id, batchId).then(
                    function (data) {
                        $scope.step = data.step;
                        $scope.count = data.count;
                        $scope.batchSize = data.batchSize;
                        $scope.uploadStatus = data.status;
                        $scope.errors = data.errors;
                    },
                    function () {
                        $scope.uploadStatus = constants.uploadBatchStatus.FAILED;
                    }
                ).finally(function () {
                    if ($scope.uploadStatus === constants.uploadBatchStatus.IN_PROGRESS) {
                        $scope.pollBatchStatus(batchId);
                    }
                });
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

        resetUploadStatus();

        cleanDisplayUrl($scope.formData);

        api.adGroupAdsPlusUpload.upload(
            $state.params.id, $scope.formData
        ).then(function (batchId) {

            $scope.uploadStatus = constants.uploadBatchStatus.IN_PROGRESS;
            $scope.step = 1;
            $scope.batchId = batchId;

            $scope.pollBatchStatus(batchId);

        }, function (data) {
            $scope.errors = data.errors;
        });
    };

    $scope.init = function () {
        api.adGroupAdsPlusUpload.getDefaults($state.params.id).then(
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

        if ($scope.uploadStatus !== constants.uploadBatchStatus.IN_PROGRESS) {
            $scope.$dismiss();
            return;
        }

        api.adGroupAdsPlusUpload.cancel($state.params.id, $scope.batchId).then(function () {
            $scope.cancelErrors = null;
        }, function (data) {
            $scope.cancelErrors = data.data.errors;
        });
    };

    $scope.isCancelDisabled = function () {
        if ($scope.uploadStatus !== constants.uploadBatchStatus.IN_PROGRESS) {
            return false;
        }

        // unsupported for cancel
        return $scope.step === 4 && $scope.count >= $scope.batchSize;
    };

    $scope.viewUploadedAds = function () {
        $modalInstance.close();

        if ($scope.user.showOnboardingGuidance) {
            api.campaignBudget.get($scope.campaign.id).then(function (data) {
                $scope.remindToAddBudget.resolve(data.available <= 0);
            });
        }
    };

    $scope.init();
    resetUploadStatus();
}]);
