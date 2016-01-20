/* globals oneApp */
oneApp.controller('AddConversionPixelModalCtrl', ['$scope', '$modalInstance', 'api', function ($scope, $modalInstance, api) {
    $scope.addConversionPixelInProgress = false;
    $scope.slug = '';
    $scope.error = false;
    $scope.errorMessage = '';

    $scope.addConversionPixel = function () {
        $scope.addConversionPixelInProgress = true;
        api.conversionPixel.post($scope.account.id, $scope.slug).then(
            function (data) {
                $modalInstance.close(data);
            },
            function (data) {
                $scope.error = true;
                if (data && data.message) {
                    $scope.errorMessage = data.message;
                }
            }
        ).finally(function () {
            $scope.addConversionPixelInProgress = false;
        });
    };

    $scope.clearError = function () {
        $scope.error = false;
        $scope.errorMessage = '';
    };
}]);
