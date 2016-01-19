/*globals oneAll */
"use strict";

oneApp.directive('zemLocations', ['config', '$state', 'regions', function(config, $state, regions) {
    return {
        restrict: 'E',
        scope: {
            selectedLocationCodes: '=zemSelectedLocationCodes',
            hasPermission: '=zemHasPermission'
        },
        templateUrl: '/partials/zem_locations.html',
        controller: ['$scope', '$compile', '$element', '$attrs', '$http', 'api', function ($scope, $compile, $element, $attrs, $http, api) {
            $scope.regions = regions;
            $scope.config = config;
            $scope.selectedLocationCode = undefined;

            $scope.selectorConfig = {
                allowClear: true,
                placeholder: 'Search',
                formatInputTooShort:
                    $scope.hasPermission('zemauth.can_set_subdivision_targeting') ?
                        'Search for Countries, DMA Codes or U.S. States<br />Ex.: "United States", "501 New York, NY", "Alabama"...' :
                        'Search for Countries or DMA Codes<br />Ex.: "United States", "501 New York, NY"...',
                minimumInputLength: 2,
                formatNoMatches: 'no matches found',
                dropdownAutoWidth: 'true',
                dropdownCssClass: 'select2-locations',
                formatResult: formatSelection
            };

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

            $scope.removeSelectedLocation = function(location) {
                $scope.resetWarnings();

                var selectedIdx = $scope.selectedLocationCodes.indexOf(location.code);
                if (selectedIdx >= 0) {
                    $scope.selectedLocationCodes.splice(selectedIdx, 1);
                }
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
            };

            function formatSelection(object) {
                if (!object.id) {
                    return object.text;
                };

                var option = regions.getByCode(object.id);

                if (regions.isCountry(option)) {
                    return object.text;
                }
     
                var element = angular.element(document.createElement('div'));
                element.text(object.text);

                var tag = angular.element(document.createElement('span'));
                tag.addClass('location-dma-tag');
                element.append(tag);

                if(regions.isDMA(option)) {
                    tag.text('DMA');
                } else if (regions.isUSState(option)) {
                    tag.text('U.S. State')
                }

                return $compile(element)($scope);
            };

            // return location codes from the currently selected location codes that
            // should be replaced by the given location code and state the reason
            function getLocationCodesToBeReplacedByLocationCode(locationCode) {
                var region = regions.getByCode(locationCode);

                // if the given location is either a DMA or a U.S. State, it should replace the United States
                if (regions.isDMA(region) || regions.isUSState(region)) {
                    if ($scope.selectedLocationCodes.indexOf('US') !== -1) {
                        return {
                            reason: 'subset',
                            locationCodes: ['US']
                        };
                    }
                // if the given location is the United States, it should replace all selected DMAs and U.S. States 
                } else if (region.code === 'US') {
                    return {
                        reason: 'broader',
                        locationCodes: $scope.selectedLocationCodes.filter(function(locationCode) {
                            var region = regions.getByCode(locationCode);

                            return regions.isDMA(region) || regions.isUSState(region);
                        })
                    };
                }
            }
            
            // return at most 3 names from the given list of location codes
            function getSomeNames(locationCodes) {
                var names = [];

                // get at most 3 names
                for (var i = 0; i < 3 && i < locationCodes.length; i++) {
                    names.push(regions.getByCode(locationCodes[i]).name);
                }

                // if more names are available, add "..."
                if (locationCodes.length > 3) {
                    names.push('...');
                }

                return names;
            }

            function getUndoProperties() {
                var locationCodesToBeReplaced = getLocationCodesToBeReplacedByLocationCode($scope.selectedLocationCode);
                
                if (locationCodesToBeReplaced) {
                    return {
                        properSelection: $scope.selectedLocationCodes.filter(function(locationCode) {
                            return locationCodesToBeReplaced.locationCodes.indexOf(locationCode) === -1;
                        }),
                        reason: locationCodesToBeReplaced.reason,
                        someReplacedNames: getSomeNames(locationCodesToBeReplaced.locationCodes)
                    };
                }
            };

            function setUndo(undoProperties) {
                // save previous state
                $scope.previousSelection = $scope.selectedLocationCodes.slice();

                $scope.selectedLocationCodes = undoProperties.properSelection;
                $scope.reason = undoProperties.reason;
                $scope.someReplacedNames = undoProperties.someReplacedNames;
                $scope.name = regions.getByCode($scope.selectedLocationCode).name;
            };
        }]
    };
}]);
