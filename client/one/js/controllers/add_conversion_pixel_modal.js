/* globals oneApp */
oneApp.controller('AddConversionPixelModalCtrl', ['$scope', '$modalInstance', '$state', '$filter', 'api', function($scope, $modalInstance, $state, $filter, api) {
    $scope.isInProgress = false;
    $scope.slug = '';

    $scope.addConversionPixel = function (slug) {
        if (!($scope.slug && $scope.slug.length)) {
            return;
        }

        $scope.isInProgress = true;
        api.conversionPixel.post($scope.account.id, $scope.slug).then(
            function(data) {
                $scope.isInProgress = false;
                $modalInstance.close(data);
            },
            function(data) {
                $scope.isInProgress = false;
            }
        );
    };
}]);
