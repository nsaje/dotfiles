/* globals oneApp */
oneApp.controller('UploadAdsModalCtrl', ['$scope', '$modalInstance', 'api', '$state', function($scope, $modalInstance, api, $state) {
    $scope.formData = {};

    $scope.upload = function() {
        api.adGroupAdsPlusUpload.upload(
            $state.params.id, $scope.formData.file, $scope.formData.batchName
        ).then(function() {
            $modalInstance.close();
        }, function(errors) {
            $scope.errors = errors;
        });
    };
}]);
