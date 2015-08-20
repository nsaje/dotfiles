/* globals oneApp */
oneApp.controller('AddConversionPixelModalCtrl', ['$scope', '$modalInstance', '$state', '$filter', 'api', function($scope, $modalInstance, $state, $filter, api) {
    $scope.addConversionPixelInProgress = false;
    $scope.slug = '';

    $scope.addConversionPixel = function (slug) {
        if (!($scope.slug && $scope.slug.length)) {
            return;
        }

        $scope.addConversionPixelInProgress = true;
        api.conversionPixel.post($scope.account.id, $scope.slug).then(
            function(data) {
                $scope.addConversionPixelInProgress = false;
                $modalInstance.close(data);
            },
            function(data) {
                $scope.addConversionPixelInProgress = false;
            }
        );
    };
}]);
