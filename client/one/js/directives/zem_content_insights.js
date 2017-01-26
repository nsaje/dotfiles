/* globals angular,$ */
'use strict';

angular.module('one.legacy').directive('zemContentInsightsLegacy', function () {
    return {
        restrict: 'E',
        scope: {
            summary: '=',
            metric: '=',
            bestPerformerRows: '=',
            worstPerformerRows: '=',
        },
        templateUrl: '/partials/zem_content_insights.html',
        controller: function ($scope, $element, $window, $timeout) {
            $scope.expanded = true;
            $scope.updateTableState = function () {
                // table can be either expanded(best and worst performers displayed side-by-side)
                // or shortened (only one table shown(best performer elements) with data bound
                // either to best or worst performers)
                var containerWidth = $('.insights-container').width();
                if (containerWidth < 800) {
                    $scope.expanded = false;
                } else {
                    // when tahb
                    $scope.expanded = true;
                    $scope.showBestPerformersCollapsed();
                }
            };

            $scope.showBestPerformersCollapsed = function () {
                $scope.collapsedDataState = 'best-performers';
                $scope.collapsedRows = $scope.bestPerformerRows;
            };

            $scope.showWorstPerformersCollapsed = function () {
                $scope.collapsedDataState = 'worst-performers';
                $scope.collapsedRows = $scope.worstPerformerRows;
            };

            $scope.$watch('bestPerformerRows', function () {
                if (!$scope.expanded && $scope.collapsedDataState === 'best-performers') {
                    $scope.collapsedRows = $scope.bestPerformerRows;
                }
            });

            $scope.$watch('worstPerformerRows', function () {
                if (!$scope.expanded && $scope.collapsedDataState === 'worst-performers') {
                    $scope.collapsedRows = $scope.worstPerformerRows;
                }
            });

            var resize = function () {
                $scope.$watch(function () {
                    return w.innerWidth();
                }, function () {
                    $scope.updateTableState();
                }, true);
                $scope.$digest();
            };

            var w = angular.element($window);
            w.bind('resize', resize);
            $scope.$on('$destroy', function () {
                w.unbind('resize', resize);
            });

            $timeout($scope.updateTableState);
            $timeout($scope.showBestPerformersCollapsed);
        },
    };
});
