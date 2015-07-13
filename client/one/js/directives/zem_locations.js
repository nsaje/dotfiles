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
            $scope.selectedDMAs = undefined;

            $scope.selectedLocationCode = undefined;

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

            var dmaNotSupportedText = undefined;

            $scope.$watch('sourcesWithoutDMASupport', function(newValue, oldValue) {
                if($scope.sourcesWithoutDMASupport && $scope.sourcesWithoutDMASupport.length) {
                    dmaNotSupportedText = $scope.sourcesWithoutDMASupport.join(", ") + " does not support DMA targeting.";
                }
            });

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

                if (dmaNotSupportedText) {
                    element.attr('popover', dmaNotSupportedText);
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

            var filterSelectedLocations = function(filterFn) {
                var filtered = [];
                for (var location, i=0; i<$scope.selectedLocationCodes.length; i++) {
                    location = regions.getByCode($scope.selectedLocationCodes[i]);
                    if (filterFn(location)) {
                        filtered.push(location);
                    }
                }
                return filtered;
            };

            var getSomeDMANames = function(additionalDMA) {
                var dmas = [];

                if (additionalDMA) {
                    dmas.push(additionalDMA);
                }

                filterSelectedLocations(function(location) {
                    if (regions.isDMA(location) && dmas.length <= 4) {
                        dmas.push((dmas.length == 3) ? '...': location.name);
                    }
                    return false;
                });

                return dmas;
            };

            var getUndoProperties = function() {
                // when US is selected remove DMAs (because they are a subset of US)
                // and add undo functionality that can undo the removal. Same for the opposite
                // situation
                var someDMAs, properSelection = [],
                    selectedLocation = regions.getByCode($scope.selectedLocationCode);

                if ($scope.selectedLocationCode === 'US') {
                    someDMAs = getSomeDMANames();
                    properSelection = filterSelectedLocations(function(location) {
                        return !regions.isDMA(location);
                    });

                } else if (regions.isDMA(selectedLocation)) {
                    someDMAs = getSomeDMANames(selectedLocation.name);
                    properSelection = filterSelectedLocations(function(location) {
                        return location.code !== 'US';
                    });
                }

                if (properSelection.length > 0 && properSelection.length !== $scope.selectedLocationCodes.length) {
                    return {
                        properSelection: properSelection.map(function(x) { return x.code; }),
                        selectedDMAs: someDMAs
                    };
                }

                return;
            };

            var setUndo = function(undoProperties) {
                // save previous state
                $scope.previousSelection = $scope.selectedLocationCodes.slice();

                $scope.selectedLocationCodes = undoProperties.properSelection;
                $scope.selectedDMAs = undoProperties.selectedDMAs;
            };

            $scope.showUndo = function() {
                return $scope.previousSelection && $scope.previousSelection.length > 0;
            };

            $scope.addLocation = function() {
                if (!$scope.selectedLocationCode) {
                    return;
                }

                $scope.resetWarnings();

                if ($scope.selectedLocationCodes === undefined) {
                    $scope.selectedLocationCodes = [];
                }

                if ($scope.selectedLocationCodes.indexOf($scope.selectedLocationCode) < 0) {
                    var undoProps = getUndoProperties();
                    if(undoProps) {
                        setUndo(undoProps);
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
                $scope.selectedDMAs = undefined;
            };
        }]
    };
}]);
