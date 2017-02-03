/* globals angular */
angular.module('one.legacy').controller('AddConversionPixelModalCtrl', function ($scope, api, audiencePixel) {
    $scope.inProgress = false;
    $scope.pixel = {name: '', audienceEnabled: false};
    $scope.audiencePixel = audiencePixel;
    $scope.validationErrors = {};
    $scope.hasErrors = false;
    $scope.title = 'Add a New Pixel';
    $scope.buttonText = 'Add Pixel';

    $scope.submit = function () {
        $scope.inProgress = true;
        api.conversionPixel.post($scope.account.id, $scope.pixel).then(
            function (data) {
                if (data.audienceEnabled) {
                    $scope.$emit('pixelAudienceEnabled', {pixel: data});
                }
                $scope.$close(data);
            },
            function (data) {
                if (data && data.errors) {
                    $scope.validationErrors = data.errors;
                } else {
                    $scope.hasErrors = true;
                }
            }
        ).finally(function () {
            $scope.inProgress = false;
        });
    };

    $scope.clearError = function () {
        $scope.hasErrors = false;
        $scope.validationErrors = {};
    };
});
