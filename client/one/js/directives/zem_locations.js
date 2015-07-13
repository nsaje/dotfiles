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

            $scope.dmaNotSupportedText = undefined;

            $scope.$watch('sourcesWithoutDMASupport', function(newValue, oldValue) {
                if($scope.sourcesWithoutDMASupport && $scope.sourcesWithoutDMASupport.length) {
                    $scope.dmaNotSupportedText = $scope.sourcesWithoutDMASupport.join(", ") + " does not support DMA targeting.";
                }
            });

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

                if (!regions.isDMA(option)) {
                    return object.text;
                }

                var element = angular.element(document.createElement('div')),
                    dmaTag = angular.element(document.createElement('span'));

                element.text(object.text);

                if ($scope.dmaNotSupportedText) {
                    element.attr('popover', $scope.dmaNotSupportedText);
                    element.attr('popover-trigger', 'mouseenter');
                    element.attr('popover-placement', 'right');
                    element.attr('popover-append-to-body', 'true');

                    // hide immediately without animation - solves a glitch when
                    // the element is selected
                    element.attr('popover-animation', 'false');
                    element.on('$destroy', function() {
                        element.trigger('mouseleave');
                    });
                }

                dmaTag.text('DMA');
                dmaTag.addClass('location-dma-tag');
                var internal = $compile(dmaTag)($scope);
                element.append(internal);

                return $compile(element)($scope);
            };

            $scope.selectorConfig = {
                allowClear: true,
                placeholder: 'Search',
                formatInputTooShort: 'Search for Countries or DMA Codes',
                minimumInputLength: 1,
                formatNoMatches: 'no matches found',
                dropdownAutoWidth: 'true',
                formatResult: formatSelection
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


                    // when US is selected remove DMAs (because they are a subset of US)
                    // and add undo functionality that can undo the removal. Same for the opposite
                    // situation
                    var others = [],
                        selectedLocation = regions.getByCode($scope.selectedLocationCode);

                    $scope.selectedDMASubsetOfUS = [];
                    if ($scope.selectedLocationCode === 'US') {
                        for (var location, i=0; i<$scope.selectedLocationCodes.length; i++) {
                            location = regions.getByCode($scope.selectedLocationCodes[i]);

                            if (regions.isDMA(location)) {
                                $scope.selectedUS = true;

                                if ($scope.selectedDMASubsetOfUS.length <= 4) {
                                    $scope.selectedDMASubsetOfUS.push(($scope.selectedDMASubsetOfUS.length == 3 ? '...': location.name));
                                }
                            } else {
                                others.push(location.code);
                            }
                        }
                    } else if (regions.isDMA(selectedLocation)) {
                        var dmas = [];
                        for (var location, i=0; i<$scope.selectedLocationCodes.length; i++) {
                            location = regions.getByCode($scope.selectedLocationCodes[i]);

                            if (regions.isDMA(location) && dmas.length <= 3) {
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
            };
        }]
    };
}]);
