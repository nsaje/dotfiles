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

            $scope.dmaNotSupportedText = undefined;

            $scope.$watch('sourcesWithoutDMASupport', function(newValue, oldValue) {
                if($scope.sourcesWithoutDMASupport && $scope.sourcesWithoutDMASupport.length) {
                    $scope.dmaNotSupportedText = "Pause " + $scope.sourcesWithoutDMASupport.join(", ") + " media " +
                        ($scope.sourcesWithoutDMASupport.length > 1 ? "sources" : "source") + " to enable DMA targeting.";
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
                minimumInputLength: 2,
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

            var getSomeDMANames = function(additionalDMA) {
                var dmas = [];

                if (additionalDMA) {
                    dmas.push(additionalDMA);
                }

                for (var location, i=0; i < $scope.selectedLocationCodes.length; i++) {
                    location = regions.getByCode($scope.selectedLocationCodes[i]);
                    if (regions.isDMA(location)) {
                        dmas.push((dmas.length === 3) ? '...': location.name);
                    }
                    if (dmas.length === 4) {
                        break;
                    }
                }

                return dmas;
            };

            var getUndoProperties = function() {
                // when US is selected remove DMAs (because they are a subset of US)
                // and add undo functionality that can undo the removal. Same for the opposite
                // situation
                var someDMAs, properSelection,
                    selectedLocation = regions.getByCode($scope.selectedLocationCode);

                if ($scope.selectedLocationCode === 'US') {
                    someDMAs = getSomeDMANames();
                    properSelection = $scope.selectedLocationCodes.filter(function(locationCode) {
                        return !regions.isDMA(regions.getByCode(locationCode));
                    });
                } else if (regions.isDMA(selectedLocation)) {
                    someDMAs = getSomeDMANames(selectedLocation.name);
                    properSelection = $scope.selectedLocationCodes.filter(function(locationCode) {
                        return locationCode !== 'US';
                    });
                }

                if (properSelection && properSelection.length !== $scope.selectedLocationCodes.length) {
                    return {
                        properSelection: properSelection,
                        selectedDMAs: someDMAs
                    };
                }
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
