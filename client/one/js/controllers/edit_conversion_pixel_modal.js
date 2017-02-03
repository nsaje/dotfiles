/* globals angular */
angular.module('one.legacy').controller('EditConversionPixelModalCtrl', function ($scope, api, pixel, audiencePixel) {
    $scope.inProgress = false;
    $scope.pixel = pixel;
    $scope.audiencePixel = audiencePixel;
    $scope.validationErrors = {};
    $scope.hasErrors = false;
    $scope.title = 'Edit Pixel';
    $scope.buttonText = 'Save Pixel';

    $scope.submit = function () {
        $scope.inProgress = true;
        api.conversionPixel.put(pixel.id, pixel).then(
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
        $scope.validationErrors = {};
        $scope.hasErrors = false;
    };
});
