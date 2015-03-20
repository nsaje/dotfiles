/* globals oneApp */
oneApp.controller('UploadAdsModalCtrl', ['$scope', '$modalInstance', 'api', '$state', '$timeout', '$filter', 'errors', function($scope, $modalInstance, api, $state, $timeout, $filter, errors) {
    $scope.errors = errors;

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

    $scope.formData = {
        batchName: getCurrentTimeString()
    };

    $scope.upload = function() {
        $scope.isInProgress = true;

        api.adGroupAdsPlusUpload.upload(
            $state.params.id, $scope.formData.file, $scope.formData.batchName
        ).then(function(batchId) {
            $scope.pollBatchStatus(batchId);
        }, function(data) {
            $scope.isInProgress = false;
            $scope.errors = data.errors;
        });
    };
    
    $scope.goToAdGroupSettings = function() {
        $modalInstance.close();
        $timeout(function() {
            $state.go('main.adGroups.settings', {id: $state.params.id});
        }, 300);
    };
}]);
