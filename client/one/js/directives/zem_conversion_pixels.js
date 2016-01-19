/*global $,oneApp,constants*/
"use strict";

oneApp.directive('zemConversionPixels', ['config', '$window', function(config, $window) {

    return {
        restrict: 'E',
        scope: {
            hasPermission: '=zemHasPermission',
            isPermissionInternal: '=zemIsPermissionInternal',
            account: '=zemAccount'
        },
        templateUrl: '/partials/zem_conversion_pixels.html',
        controller: ['$scope', '$element', '$modal', 'api', 'zemFilterService', function ($scope, $element, $modal, api, zemFilterService) {
            $scope.conversionPixels = [];
            $scope.listInProgress = false;
            $scope.listError = false;
            $scope.orderField = 'slug';
            $scope.orderReverse = false;
            $scope.tagPrefix = '';

            $scope.getConversionPixels = function () {
                $scope.listInProgress = true;
                api.conversionPixel.list($scope.account.id).then(
                    function (data) {
                        $scope.conversionPixels = data.rows;
                        $scope.tagPrefix = data.tagPrefix;
                    },
                    function (data) {
                        $scope.listError = true;
                    }
                ).finally(function () {
                    $scope.listInProgress = false;
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

            $scope.getConversionPixelTag = function (url) {
                return '<img src="' + url + '" height="1" width="1" border="0" alt="" />';
            };

            $scope.getConversionPixels();
        }]
    };
}]);
