/*globals oneApp,constants,options,moment*/
oneApp.controller('AccountAccountCtrl', ['$scope', '$state', '$q', '$timeout', '$modal', 'api', 'zemFilterService', function ($scope, $state, $q, $timeout, $modal, api, zemFilterService) {
    $scope.conversionPixels = [];
    $scope.listPixelsInProgress = false;
    $scope.listPixelsError = false;
    $scope.pixelOrderField = 'slug';
    $scope.pixelOrderReverse = false;
    $scope.conversionPixelTagPrefix = '';

    $scope.getConversionPixels = function () {
        $scope.listPixelsInProgress = true;
        api.conversionPixel.list($scope.account.id).then(
            function (data) {
                $scope.conversionPixels = data.rows;
                $scope.conversionPixelTagPrefix = data.conversionPixelTagPrefix;
            },
            function (data) {
                $scope.listPixelsError = true;
            }
        ).finally(function () {
            $scope.listPixelsInProgress = false;
        });
    };

    $scope.addConversionPixel = function () {
        var modalInstance = $modal.open({
            templateUrl: '/partials/add_conversion_pixel_modal.html',
            controller: 'AddConversionPixelModalCtrl',
            windowClass: 'modal',
            scope: $scope
        });

        modalInstance.result.then(function(conversionPixel) {
            $scope.conversionPixels.push(conversionPixel);
        });

        return modalInstance;
    };

    $scope.archiveConversionPixel = function (conversionPixel) {
        conversionPixel.requestInProgress = true;
        conversionPixel.error = false;
        api.conversionPixel.archive(conversionPixel.id).then(
            function (data) {
                conversionPixel.archived = data.archived;
            },
            function (data) {
                conversionPixel.error = true;
            }
        ).finally(function () {
            conversionPixel.requestInProgress = false;
        });
    };

    $scope.restoreConversionPixel = function (conversionPixel) {
        conversionPixel.requestInProgress = true;
        conversionPixel.error = false;
        api.conversionPixel.restore(conversionPixel.id).then(
            function (data) {
                conversionPixel.archived = data.archived;
            },
            function (data) {
                conversionPixel.error = true;
            }
        ).finally(function () {
            conversionPixel.requestInProgress = false;
        });
    };

    $scope.copyConversionPixelTag = function (conversionPixel) {
        var scope = $scope.$new(true);
        scope.conversionPixelTag = $scope.getConversionPixelTag(conversionPixel.url);

        var modalInstance = $modal.open({
            templateUrl: '/partials/copy_conversion_pixel_modal.html',
            windowClass: 'modal',
            scope: scope
        });

        return modalInstance;
    };

    $scope.filterConversionPixels = function (conversionPixel) {
        if (zemFilterService.getShowArchived()) {
            return true;
        }

        return !conversionPixel.archived;
    };

    $scope.getConversionPixels();
}]);
