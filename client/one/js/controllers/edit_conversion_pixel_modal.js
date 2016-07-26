/* globals oneApp */
oneApp.controller('EditConversionPixelModalCtrl', ['$scope', '$modalInstance', 'api', 'pixel', function ($scope, $modalInstance, api, pixel) {
    $scope.inProgress = false;
    $scope.pixel = pixel;
    $scope.error = false;
    $scope.errorMessage = '';
    $scope.title = 'Edit Pixel';
    $scope.buttonText = 'Save Pixel';

    $scope.submit = function () {
        $scope.inProgress = true;
        api.conversionPixel.rename(pixel).then(
            function (data) {
                $modalInstance.close(data);
            },
            function (data) {
                $scope.error = true;
                $scope.errorMessage = data.errors.name.join(' ');
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
