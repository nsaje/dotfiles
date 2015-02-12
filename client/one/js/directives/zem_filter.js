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

            // this updates everytime user changes the settings
            $scope.filteredSourcesNoUserSettings = $scope.filteredSources.slice();
            $scope.showArchivedNoUserSettings = $scope.showArchived;

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
                    $scope.updateUserSettings();
                }
            };

            $scope.updateUserSettings = function () {
                $scope.filteredSources = $scope.filteredSourcesNoUserSettings.slice();
                $scope.showArchived = $scope.showArchivedNoUserSettings;
            };

            $scope.updateService = function () {
                zemFilterService.filteredSources = $scope.filteredSourcesNoUserSettings.slice();
                zemFilterService.showArchived = $scope.showArchivedNoUserSettings;
            };

            api.availableSources.list().then(function (data) {
                $scope.sources = data.data.sources;
            });

            $scope.addFilteredSource = function (sourceId) {
                if (!sourceId || sourceId === '') {
                    return;
                }

                $scope.filteredSourcesNoUserSettings.push(sourceId);
                $scope.filteredSourcesNoUserSettings.sort(function (a, b) { return parseInt(a) - parseInt(b); });

                $scope.updateService();

                $scope.sourceId = '';
            };

            $scope.isSourceFiltered = function (source) {
                for (var i = 0; i < $scope.filteredSourcesNoUserSettings.length; i++) {
                    if ($scope.filteredSourcesNoUserSettings[i] === source.id) {
                        return true;
                    }
                }

                return false;
            };

            $scope.isSourceNotFiltered = function (source) {
                return !$scope.isSourceFiltered(source);
            };

            $scope.isFilterOn = function () {
                return $scope.filteredSourcesNoUserSettings.length > 0;
            };

            $scope.removeFilters = function () {
                $scope.filteredSourcesNoUserSettings = [];
                $scope.updateUserSettings();
                $scope.updateService();
            };

            $scope.removeFilteredSource = function (sourceId) {
                for (var i = 0; i < $scope.filteredSourcesNoUserSettings.length; i++) {
                    if ($scope.filteredSourcesNoUserSettings[i] === sourceId) {
                        $scope.filteredSourcesNoUserSettings.splice(i, 1);
                        break;
                    }
                }

                $scope.updateService();
            };

            $scope.$watch('filteredSourcesNoUserSettings', function (newValue, oldValue) {
                $scope.updateService();
            }, true);

            $scope.$watch('showArchivedNoUserSettings', function () {
                $scope.updateService();
            });
        }]
    };
}]);
