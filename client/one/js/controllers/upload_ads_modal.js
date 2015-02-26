/* globals oneApp */
oneApp.controller('UploadAdsModalCtrl', ['$scope', '$modalInstance', 'api', '$state', '$timeout', function($scope, $modalInstance, api, $state, $timeout) {
    $scope.formData = {};

    $scope.upload = function() {
        $scope.isInProgress = true;

        api.adGroupAdsPlusUpload.upload(
            $state.params.id, $scope.formData.file, $scope.formData.batchName
        ).then(function(batchId) {
            pollBatchStatus(batchId);
        }, function(errors) {
            $scope.isInProgress = false;
            $scope.errors = errors;
        });
    };

    var pollBatchStatus = function(batchId) {
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
                    pollBatchStatus(batchId);
                });
            }, 1000);
        }
    };
}]);
