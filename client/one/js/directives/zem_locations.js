/*globals oneAll */
"use strict";

oneApp.directive('zemLocations', ['config', '$state', 'regions', function(config, $state, regions) {
    return {
        restrict: 'E',
        scope: {
            selectedLocationCodes: '=zemSelectedLocationCodes',
            sourcesWithoutDMASupport: '=zemSourcesWithoutDmaSupport'
        },
        templateUrl: '/partials/zem_locations.html',
        controller: ['$scope', '$compile', '$element', '$attrs', '$http', 'api', function ($scope, $compile, $element, $attrs, $http, api) {
            $scope.regions = regions;
            $scope.config = config;

            $scope.previousSelection = undefined;
            $scope.selectedDMASubsetOfUS = undefined;
            $scope.selectedUS = false;
            $scope.warnDMANotSupported = false;

            $scope.selectedLocations = function() {
                if (!$scope.selectedLocationCodes)
                    return [];

                var location, locations = [];
                for (var i=0; i<$scope.selectedLocationCodes.length; i++) {
                    location = regions.getByCode($scope.selectedLocationCodes[i]);

                    if (location) {
                        locations.push(location);
                    }
                }

                return locations;
            };

            $scope.selectedLocationCode = undefined;

            var formatSelection = function(object) {
                if (!object.id) {
                    return object.text;
                };

                var option = regions.getByCode(object.id);

                if (!$scope.isDMA(option)) {
                    return object.text;
                }

                var element = angular.element(document.createElement('span')),
                    dmaTag = angular.element(document.createElement('span'));

                element.text(object.text);
                dmaTag.text('DMA');
                dmaTag.addClass('location-dma-tag');
                var internal = $compile(dmaTag)($scope);
                element.append(internal);

                return $compile(element)($scope);
            };

            $scope.selectorConfig = {
                allowClear: true,
                placeholder: 'Search',
                formatInputTooShort: 'type to start searching',
                formatNoMatches: 'no matches found',
                dropdownAutoWidth: 'true',
                formatResult: formatSelection
            };

            $scope.isCountry = function(location) {
                return location.type === 'C';
            };

            $scope.isDMA = function(location) {
                return location.type === 'D';
            };

            $scope.isLocationSelected = function(location) {
                return $scope.selectedLocationCodes.indexOf(location.code) >= 0;
            };

            $scope.removeSelectedLocation = function(location) {
                $scope.resetWarnings();

                var selectedIdx = $scope.selectedLocationCodes.indexOf(location.code);
                if (selectedIdx >= 0) {
                    $scope.selectedLocationCodes.splice(selectedIdx, 1);
                }
            };

            $scope.addLocation = function() {
                if (!$scope.selectedLocationCode || $scope.selectedLocationCode === undefined) {
                    return;
                }

                $scope.resetWarnings();

                if ($scope.selectedLocationCodes === undefined) {
                    $scope.selectedLocationCodes = [];
                }

                if ($scope.selectedLocationCodes.indexOf($scope.selectedLocationCode) < 0) {

                    var selectedLocation = regions.getByCode($scope.selectedLocationCode);

                    // check if all media sources support DMA targeting
                    if (selectedLocation.type === 'D' && $scope.sourcesWithoutDMASupport
                        && $scope.sourcesWithoutDMASupport.length > 0) {

                            $scope.warnDMANotSupported = true;
                            $scope.selectedLocationCode = '';
                            return;
                    }

                    // when US is selected remove DMAs (because they are a subset of US)
                    // and add undo functionality that can undo the removal. Same for the opposite
                    // situation
                    var others = [];

                    $scope.selectedDMASubsetOfUS = [];
                    if ($scope.selectedLocationCode === 'US') {
                        for (var location, i=0; i<$scope.selectedLocationCodes.length; i++) {
                            location = regions.getByCode($scope.selectedLocationCodes[i]);

                            if ($scope.isDMA(location)) {
                                $scope.selectedUS = true;

                                if ($scope.selectedDMASubsetOfUS.length <= 4) {
                                    $scope.selectedDMASubsetOfUS.push(($scope.selectedDMASubsetOfUS.length == 3 ? '...': location.name));
                                }
                            } else {
                                others.push(location.code);
                            }
                        }
                    } else if ($scope.isDMA(selectedLocation)) {
                        var dmas = [];
                        for (var location, i=0; i<$scope.selectedLocationCodes.length; i++) {
                            location = regions.getByCode($scope.selectedLocationCodes[i]);

                            if ($scope.isDMA(location) && dmas.length <= 3) {
                                // max 2 DMAs, because one extra (the selected one) will be added
                                // in case of US selection
                                dmas.push((dmas.length == 2 ? '...': location.name));
                            }

                            if (location.code !== 'US'){
                                others.push(location.code);
                            }
                        }

                        if (others.length !== $scope.selectedLocationCodes.length) {
                            $scope.selectedUS = false;
                            $scope.selectedDMASubsetOfUS.push(selectedLocation.name);
                            $scope.selectedDMASubsetOfUS.push.apply(dmas);
                        }
                    }


                    if ($scope.selectedDMASubsetOfUS.length > 0) {
                        // save previous state
                        $scope.previousSelection = $scope.selectedLocationCodes.slice();

                        // set state without DMAs
                        $scope.selectedLocationCodes = others;
                    }

                    $scope.selectedLocationCodes.push($scope.selectedLocationCode);
                }
                $scope.selectedLocationCode = '';
            };

            $scope.undo = function() {
                if($scope.previousSelection) {
                    $scope.selectedLocationCodes = $scope.previousSelection;
                    $scope.resetWarnings();
                }
            };

            $scope.resetWarnings = function() {
                $scope.previousSelection = undefined;
                $scope.selectedDMASubsetOfUS = undefined;
                $scope.warnDMANotSupported = false;
            };
        }]
    };
}]);
