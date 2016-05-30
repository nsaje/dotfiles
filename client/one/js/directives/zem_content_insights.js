/* globals oneApp,angular,$ */
'use strict';

oneApp.directive('zemContentInsights', function () {
    return {
        restrict: 'E',
        scope: {
            summary: '=',
            metric: '=',
            bestPerformerRows: '=',
            worstPerformerRows: '=',
        },
        templateUrl: '/partials/zem_content_insights.html',
        controller: ['$scope', '$element', '$window', '$timeout', function ($scope, $element, $window, $timeout) {
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
                    $scope.updateCollapsedTableState();
                }
            };

            $scope.updateCollapsedTableState = function () {
                $scope.collapsedDataState = 'best-performers';
                $scope.collapsedRows = $scope.bestPerformerRows;
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

            var w = angular.element($window);
            w.bind('resize', function () {
                $scope.$watch(function () {
                    return w.innerWidth();
                }, function () {
                    $scope.updateTableState();
                }, true);
                $scope.$digest();
            });

            $timeout($scope.updateTableState, 0);
            $timeout($scope.updateCollapsedTableState, 0);
        }],
    };
});
