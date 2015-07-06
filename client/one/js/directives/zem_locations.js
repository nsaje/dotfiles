/*globals oneAll, locationsList */
"use strict";

oneApp.directive('zemLocations', ['config', '$state', function(config, $state) {
    return {
        restrict: 'E',
        templateUrl: '/partials/zem_locations.html',
        controller: ['$scope', '$element', '$attrs', '$http', 'api', function ($scope, $element, $attrs, $http, api) {
            // TODO: only for testing
            $scope.locations = locationsList;

            $scope.selectedLocations = ['GB', '693', '592', '593', 'SI'];

            $scope.selectorConfig = {
                allowClear: true,
                placeholder: 'Search',
                containerCssClass: 'add-source-filter-locations',
                dropdownCssClass: 'select2-locations',
                formatInputTooShort: 'type to start searching',
                formatNoMatches: 'no matches found',
                dropdownAutoWidth: 'true'
            };

            $scope.isCountry = function(location) {
                return location.type === 'C';
            };

            $scope.isDMA = function(location) {
                return location.type === 'D';
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
