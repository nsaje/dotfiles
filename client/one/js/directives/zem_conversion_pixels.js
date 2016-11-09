/*global $,angular,constants*/
'use strict';

angular.module('one.legacy').directive('zemConversionPixels', function (config, $window) {

    return {
        restrict: 'E',
        scope: {
            hasPermission: '=zemHasPermission',
            isPermissionInternal: '=zemIsPermissionInternal',
            account: '=zemAccount'
        },
        templateUrl: '/partials/zem_conversion_pixels.html',
        controller: function ($scope, $element, $uibModal, api, zemFilterService) {
            $scope.conversionPixels = [];
            $scope.listInProgress = false;
            $scope.listError = false;
            $scope.orderField = 'name';
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
                var modalInstance = $uibModal.open({
                    templateUrl: '/partials/conversion_pixel_modal.html',
                    controller: 'AddConversionPixelModalCtrl',
                    scope: $scope,
                    backdrop: 'static',
                    keyboard: false,
                    resolve: {
                        audiencePixel: function () {
                            var pixies = $scope.conversionPixels.filter(function (pixie) {
                                return pixie.audienceEnabled;
                            });
                            return pixies.length > 0 ? pixies[0] : null;
                        }
                    }
                });

                modalInstance.result.then(function (conversionPixel) {
                    if (conversionPixel.audienceEnabled) {
                        $scope.conversionPixels.map(function (pixie) {
                            if (pixie.audienceEnabled) {
                                pixie.audienceEnabled = false;
                            }
                        });
                    }
                    $scope.conversionPixels.push(conversionPixel);
                });

                return modalInstance;
            };

            $scope.editConversionPixel = function (pixel) {
                var modalInstance = $uibModal.open({
                    templateUrl: '/partials/conversion_pixel_modal.html',
                    controller: 'EditConversionPixelModalCtrl',
                    scope: $scope,
                    backdrop: 'static',
                    keyboard: false,
                    resolve: {
                        pixel: function () {
                            return {id: pixel.id, name: pixel.name, audienceEnabled: pixel.audienceEnabled};
                        },
                        audiencePixel: function () {
                            var pixies = $scope.conversionPixels.filter(function (pixie) {
                                return pixie.audienceEnabled;
                            });
                            return pixies.length > 0 ? pixies[0] : null;
                        }
                    }
                });

                modalInstance.result.then(function (conversionPixel) {
                    $scope.conversionPixels.forEach(function (pixel) {
                        if (pixel.id === conversionPixel.id) {
                            pixel.name = conversionPixel.name;
                            pixel.audienceEnabled = conversionPixel.audienceEnabled;
                        }
                    });
                });

                return modalInstance;
            };

            $scope.archiveConversionPixel = function (conversionPixel) {
                conversionPixel.requestInProgress = true;
                conversionPixel.error = false;
                api.conversionPixel.archive(conversionPixel).then(
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
                api.conversionPixel.restore(conversionPixel).then(
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
                scope.conversionPixelTag = $scope.getConversionPixelTag(
                    conversionPixel.name, conversionPixel.url);

                var modalInstance = $uibModal.open({
                    templateUrl: '/partials/copy_conversion_pixel_modal.html',
                    scope: scope,
                    backdrop: 'static',
                    keyboard: false,
                });

                return modalInstance;
            };

            $scope.filterConversionPixels = function (conversionPixel) {
                if (zemFilterService.getShowArchived()) {
                    return true;
                }

                return !conversionPixel.archived;
            };

            $scope.getConversionPixelTag = function (name, url) {
                return '<!-- ' + name + '-->\n<img src="' + url + '" height="1" width="1" border="0" alt="" />';
            };

            $scope.getConversionPixels();
        }
    };
});
