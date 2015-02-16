/*global $,oneApp,constants*/
"use strict";

oneApp.directive('zemFilter', ['config', function(config) {
    return {
        restrict: 'E',
        templateUrl: '/partials/zem_filter.html',
        scope: {
            hasPermission: '=zemHasPermission',
            isPermissionInternal: '=zemIsPermissionInternal'
        },
        link: function ($scope, element) {
            element.on('click', function(e) {
                e.stopPropagation();
            });
        },
        controller: ['$scope', 'zemFilterService', 'zemUserSettings', 'api', function ($scope, zemFilterService, zemUserSettings, api) {
            $scope.availableSources = [];
            $scope.config = config;

            $scope.showArchivedSelected = zemFilterService.getShowArchived();

            api.availableSources.list().then(function (data) {
                $scope.availableSources = data.data.sources;
            });

            $scope.addFilteredSource = function (sourceId) {
                if (!sourceId || sourceId === '') {
                    return;
                }

                zemFilterService.addFilteredSource(sourceId);
                $scope.sourceIdToFilter = '';
            };

            $scope.exclusivelyFilterSource = function (sourceId) {
                zemFilterService.exclusivelyFilterSource(sourceId);
            };

            $scope.isSourceFiltered = function (source) {
                return zemFilterService.isSourceFiltered(source.id);
            };

            $scope.isSourceNotFiltered = function (source) {
                return !$scope.isSourceFiltered(source);
            };

            $scope.isFilterOn = function () {
                return zemFilterService.isSourceFilterOn();
            };

            $scope.removeFiltering = function () {
                zemFilterService.removeFiltering();
            };

            $scope.removeFilteredSource = function (sourceId) {
                zemFilterService.removeFilteredSource(sourceId);
            };

            $scope.$watch('showArchivedSelected', function (newValue, oldValue) {
                if (newValue !== oldValue) {
                    zemFilterService.setShowArchived(newValue);
                }
            });

            $scope.$on('$locationChangeStart', function() {
                // ui-bootstrap registers a listener on $locationChangeSuccess event
                // which closes the dropdown when the event triggers.
                // We don't want the dropdown to close upon changing the query string
                // parameters, so we remove all listeners on this event.
                // This can be done here because dropdown registers the listener on
                // the scope of the controller/directive that initialized it rather
                // than on it's isolated scope.
                $scope.$$listeners.$locationChangeSuccess = [];
            });

            $scope.$on('$stateChangeSuccess', function() {
                // Upon state change we do want to close the dropdown.
                $scope.isFilterOpen = false;
            });
        }]
    };
}]);
