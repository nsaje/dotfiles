/*globals oneAll, locationsList, locationsLookup */
"use strict";

oneApp.directive('zemLocations', ['config', '$state', function(config, $state) {
    return {
        restrict: 'E',
        scope: {
            selectedLocationCodes: '=zemSelectedLocationCodes',
            sourcesWithoutDMASupport: '=zemSourcesWithoutDmaSupport'
        },
        templateUrl: '/partials/zem_locations.html',
        controller: ['$scope', '$compile', '$element', '$attrs', '$http', 'api', function ($scope, $compile, $element, $attrs, $http, api) {
            $scope.locations = locationsList;
            $scope.config = config;

            $scope.previousSelection = undefined;
            $scope.dmaChange = undefined;
            $scope.warnDMANotSupported = false;

            $scope.selectedLocations = function() {
                if (!$scope.selectedLocationCodes)
                    return [];

                var location, locations = [];
                for (var i=0; i<$scope.selectedLocationCodes.length; i++) {
                    location = locationsLookup.getLocation($scope.selectedLocationCodes[i]);

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

                var option = locationsLookup.getLocation(object.id);

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
                var selectedIdx = $scope.selectedLocationCodes.indexOf(location.code);
                if (selectedIdx >= 0) {
                    $scope.selectedLocationCodes.splice(selectedIdx, 1);
                }
            };

            $scope.addLocation = function() {
                if (!$scope.selectedLocationCode || $scope.selectedLocationCode === undefined) {
                    return;
                }

                if ($scope.selectedLocationCodes === undefined) {
                    $scope.selectedLocationCodes = [];
                }

                if ($scope.selectedLocationCodes.indexOf($scope.selectedLocationCode) < 0) {

                    var selectedLocation = locationsLookup.getLocation($scope.selectedLocationCode);

                    // check if all media sources support DMA targeting
                    if (selectedLocation.type === 'D' && $scope.sourcesWithoutDMASupport) {
                        $scope.warnDMANotSupported = true;
                        $scope.selectedLocationCode = '';
                        return;
                    }

                    // when US is selected remove DMAs (because they are a subset of US)
                    // and add undo functionality that can undo the removal
                    if ($scope.selectedLocationCode === 'US') {

                        var location,
                            hasDMAs = false,
                            selectedDMAs = [],
                            nDMAs = 3,
                            dmas = [],
                            others = [];

                        for (var i=0; i<$scope.selectedLocationCodes.length; i++) {

                            location = locationsLookup.getLocation($scope.selectedLocationCodes[i]);

                            if ($scope.isDMA(location)) {
                                hasDMAs = true;

                                // remember DMAs, 1 more so we can see if we need to append "..." at the end
                                if (dmas.length > nDMAs)
                                    continue;

                                dmas.push(location);

                            }
                            else {
                                others.push(location.code);
                            }
                        }

                        if (hasDMAs) {
                            // save previous state
                            $scope.previousSelection = $scope.selectedLocationCodes.slice();

                            // set state without DMAs
                            $scope.selectedLocationCodes = others;

                            // set text
                            $scope.dmaChange = '';
                            for (var i=0; i<dmas.length; i++) {
                                if ($scope.dmaChange.length > 0) {
                                    $scope.dmaChange += ', ';
                                }

                                if (i > nDMAs) {
                                    $scope.dmaChange += '...';
                                } else {
                                    $scope.dmaChange += dmas[i].name;
                                }
                            }
                        }
                    }
                    $scope.selectedLocationCodes.push($scope.selectedLocationCode);
                }
                $scope.selectedLocationCode = '';
            };

            $scope.undo = function() {
                if($scope.previousSelection) {
                    $scope.selectedLocationCodes = $scope.previousSelection;
                    $scope.previousSelection = undefined;
                    $scope.dmaChange = undefined;
                }
            };
        }]
    };
}]);
