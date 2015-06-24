/* globals oneApp */
oneApp.controller('UploadAdsModalCtrl', ['$scope', '$modalInstance', 'api', '$state', '$timeout', '$filter', function($scope, $modalInstance, api, $state, $timeout, $filter) {
    $scope.errors = null;
    $scope.formData = {};

    var getCurrentTimeString = function() {
        var datetime = new Date();  // get current local time

        // add UTC timezone offset to simulate time in UTC timezone
        var timestamp = datetime.getTime() + datetime.getTimezoneOffset() * 60 * 1000;

        datetime = new Date(timestamp + $scope.user.timezoneOffset * 1000);
        return $filter('date')(datetime, 'M/d/yyyy h:mm a');
    };

    $scope.pollBatchStatus = function(batchId) {
        if ($scope.isInProgress) {
            $timeout(function() {
                api.adGroupAdsPlusUpload.checkStatus($state.params.id, batchId).then(
                    function(data) {
                        if (data.status === constants.uploadBatchStatus.DONE) {
                            $scope.isInProgress = false;
                            $modalInstance.close();
                        } else if (data.status === constants.uploadBatchStatus.FAILED) {
                            $scope.isInProgress = false;
                            $scope.errors = data.errors;
                        }
                        $scope.countUploaded = data.count;
                        $scope.countAll = data.all;
                    },
                    function(data) {
                        $scope.isInProgress = false;
                    }
                ).finally(function() {
                    $scope.pollBatchStatus(batchId);
                });
            }, 1000);
        }
    };

    var replaceStart = /^https?:\/\//;
    var replaceEnd = /\/$/;
    function cleanDisplayUrl(data) {
        if(data.displayUrl === undefined) {
            return;
        }

        data.displayUrl = data.displayUrl.replace(replaceStart,'');
        data.displayUrl = data.displayUrl.replace(replaceEnd, '');
    };

    $scope.clearErrors = function(name) {
        if (!$scope.errors) {
            return;
        }
        delete $scope.errors[name];
    };

    $scope.upload = function() {
        if ($scope.isInProgress) {
            return;
        }

        $scope.isInProgress = true;
        $scope.countUploaded = 0;
        $scope.countAll = 0;
        $scope.errors = null;        

        cleanDisplayUrl($scope.formData);

        api.adGroupAdsPlusUpload.upload(
            $state.params.id, $scope.formData
        ).then(function(batchId) {
            $scope.pollBatchStatus(batchId);
        }, function(data) {
            $scope.isInProgress = false;
            $scope.countUploaded = 0;
            $scope.countAll = 0;
            $scope.errors = data.errors;
        });
    };

    $scope.init = function() {
        api.adGroupAdsPlusUpload.getDefaults($state.params.id).then(
            function(data) {
                angular.extend($scope.formData, data.defaults);
                $scope.formData.batchName = getCurrentTimeString();
            });
    };

    $scope.init();
}]);
