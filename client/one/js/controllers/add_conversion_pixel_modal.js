/* globals angular */
angular.module('one.legacy').controller('AddConversionPixelModalCtrl', ['$scope', 'api', function ($scope, api) {
    $scope.inProgress = false;
    $scope.pixel = {name: '', outbrainSync: false};
    $scope.error = false;
    $scope.errorMessage = '';
    $scope.title = 'Add a New Pixel';
    $scope.buttonText = 'Add Pixel';

    $scope.submit = function () {
        $scope.inProgress = true;
        api.conversionPixel.post($scope.account.id, $scope.pixel.name, $scope.pixel.outbrainSync).then(
            function (data) {
                $scope.$close(data);
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
