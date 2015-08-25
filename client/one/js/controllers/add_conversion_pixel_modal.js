/* globals oneApp */
oneApp.controller('AddConversionPixelModalCtrl', ['$scope', '$modalInstance', '$state', '$filter', 'api', function($scope, $modalInstance, $state, $filter, api) {
    $scope.addConversionPixelInProgress = false;
    $scope.slug = '';
    $scope.error = null;

    $scope.addConversionPixel = function (slug) {
        $scope.addConversionPixelInProgress = true;
        api.conversionPixel.post($scope.account.id, $scope.slug).then(
            function(data) {
                $scope.addConversionPixelInProgress = false;
                $modalInstance.close(data);
            },
            function(data) {
                if (data && data.message) {
                    $scope.error = data.message;
                }
                $scope.addConversionPixelInProgress = false;
            }
        );
    };

    $scope.clearError = function () {
        $scope.error = null;
    };
}]);
