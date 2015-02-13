/*global $,oneApp,constants*/
"use strict";

oneApp.directive('zemFilter', ['config', function(config) {
    return {
        restrict: 'E',
        templateUrl: '/partials/zem_filter.html',
        link: function ($scope, element) {
            element.on('click', function(e) {
                e.stopPropagation();
            });
        },
        controller: ['$scope', '$location', 'zemFilterService', 'zemUserSettings', 'api', function ($scope, $location, zemFilterService, zemUserSettings, api) {
            $scope.sources = [];
            $scope.config = config;

            // this updates when user closes the dropdown
            $scope.filteredSources = zemFilterService.filteredSources;
            $scope.showArchived = zemFilterService.showArchived;

            var userSettings = zemUserSettings.getInstance($scope, 'main');

            if ($scope.hasPermission('zemauth.filter_sources')) {
                userSettings.registerGlobal('filteredSources');
            }

            if ($scope.hasPermission('zemauth.view_archived_entities')) {
                userSettings.registerGlobal('showArchived');
            }

            $scope.onToggle = function (open) {
                if (!open) {
                    $scope.updateService();
                }
            };

            $scope.updateService = function () {
                zemFilterService.filteredSources = $scope.filteredSources.slice();
                zemFilterService.showArchived = $scope.showArchived;
            };

            api.availableSources.list().then(function (data) {
                $scope.sources = data.data.sources;
            });

            $scope.addFilteredSource = function (sourceId) {
                if (!sourceId || sourceId === '') {
                    return;
                }

                $scope.filteredSources.push(sourceId);
                $scope.filteredSources.sort(function (a, b) { return parseInt(a) - parseInt(b); });

                $scope.updateService();

                $scope.sourceId = '';
            };

            $scope.isSourceFiltered = function (source) {
                for (var i = 0; i < $scope.filteredSources.length; i++) {
                    if ($scope.filteredSources[i] === source.id) {
                        return true;
                    }
                }

                return false;
            };

            $scope.isSourceNotFiltered = function (source) {
                return !$scope.isSourceFiltered(source);
            };

            $scope.isFilterOn = function () {
                return $scope.filteredSources.length > 0;
            };

            $scope.removeFilters = function () {
                $scope.filteredSources = [];
                $scope.updateService();
            };

            $scope.removeFilteredSource = function (sourceId) {
                for (var i = 0; i < $scope.filteredSources.length; i++) {
                    if ($scope.filteredSources[i] === sourceId) {
                        $scope.filteredSources.splice(i, 1);
                        break;
                    }
                }

                $scope.updateService();
            };

            $scope.$watch('filteredSources', function (newValue, oldValue) {
                $scope.updateService();
            }, true);

            $scope.$watch('showArchived', function () {
                $scope.updateService();
            });

            $scope.$on('$locationChangeStart', function() {
                // ui-bootstrap registers a listener on $locationChangeSuccess event
                // which closes the dropdown.
                // We don't want the dropdown to close on changing only the query string
                // parameters, so we delete this event listener.
                // We do this here because dropdown controller sets after this scope has
                // already initialized (however it doesn't use an isolated scope, so the
                // event listener is registered on this scope)
                $scope.$$listeners.$locationChangeSuccess = [];
            });

            $scope.$on('$stateChangeSuccess', function() {
                // Upon state change we do want to close the dropdown.
                $scope.isFilterOpen = false;
            });
        }]
    };
}]);
