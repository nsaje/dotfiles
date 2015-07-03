/*globals oneAll*/
"use strict";

oneApp.directive('zemLocations', ['config', '$state', function(config, $state) {
    return {
        restrict: 'E',
        templateUrl: '/partials/zem_locations.html',
        controller: ['$scope', '$element', '$attrs', '$http', 'api', function ($scope, $element, $attrs, $http, api) {
            // TODO: only for testing
            $scope.locations = [
                {code: 'US', name: 'United states', type: 'country'},
                {code: '693', name: 'Some DMA', type: 'DMA'},
                {code: 'SL', name: 'Slovenia', type: 'country'},
                {code: 'GB', name: 'United Kingdom', type: 'country'},
            ];

            $scope.selectedLocations = ['GB', '693'];

            $scope.selectorConfig = {
                allowClear: false,
                minimumInputLength: 1,
                placeholder: 'Search',
                containerCssClass: 'add-source-filter',
                dropdownCssClass: 'select2-filter',
                formatInputTooShort: 'type to start searching',
                formatNoMatches: 'no matches found'
            };

            $scope.isCountry = function(location) {
                return location.type === 'country';
            };

            $scope.isDMA = function(location) {
                return location.type === 'DMA';
            };

            $scope.isLocationSelected = function(location) {
                return $scope.selectedLocations.indexOf(location.code) >= 0;
            };

            $scope.removeSelectedLocation = function(location) {
                var selectedIdx = $scope.selectedLocations.indexOf(location.code);
                if (selectedIdx >= 0) {
                    $scope.selectedLocations.splice(selectedIdx, 1);
                }
            };

            $scope.addLocation = function() {
                if (!$scope.selectedLocation || $scope.selectedLocation === '') {
                    return;
                }

                if ($scope.selectedLocations.indexOf($scope.selectedLocation) < 0) {
                    $scope.selectedLocations.push($scope.selectedLocation);
                }
                $scope.selectedLocation = '';
            };

        }]
    };
}]);
