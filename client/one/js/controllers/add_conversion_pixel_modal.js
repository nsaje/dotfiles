/* globals oneApp */
oneApp.controller('AddConversionPixelModalCtrl', ['$scope', '$modalInstance', 'api', function ($scope, $modalInstance, api) {
    $scope.inProgress = false;
    $scope.pixel = {name: ''};
    $scope.error = false;
    $scope.errorMessage = '';
    $scope.title = 'Add a New Pixel';
    $scope.buttonText = 'Add Pixel';

    $scope.submit = function () {
        $scope.inProgress = true;
        api.conversionPixel.post($scope.account.id, $scope.pixel.name).then(
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
            $scope.inProgress = false;
        });
    };

    $scope.clearError = function () {
        $scope.error = false;
        $scope.errorMessage = '';
    };
}]);
