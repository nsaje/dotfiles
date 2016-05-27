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
            $scope.updateExpanded = function () {
                var containerWidth = $('.insights-container').width();
                console.log(containerWidth);
                if (containerWidth < 800) {
                    $scope.expanded = false;
                } else {
                    $scope.expanded = true;
                    $scope.setDefaultShortened();
                }
            };

            $scope.setDefaultShortened = function () {
                $scope.shortenedShown = 'best-performers';
                $scope.shortenedRows = $scope.bestPerformerRows;
            };

            $scope.showBestPerformers = function () {
                $scope.shortenedShown = 'best-performers';
                $scope.shortenedRows = $scope.bestPerformerRows;
            };

            $scope.showWorstPerformers = function () {
                $scope.shortenedShown = 'worst-performers';
                $scope.shortenedRows = $scope.worstPerformerRows;
            };

            $scope.$watch('bestPerformerRows', function () {
                if (!$scope.expanded && $scope.shortenedShown === 'best-performers') {
                    $scope.shortenedRows = $scope.bestPerformerRows;
                }
            });

            var w = angular.element($window);
            w.bind('resize', function () {
                $scope.$watch(function () {
                    return w.innerWidth();
                }, function () {
                    $scope.updateExpanded();
                }, true);
                $scope.$digest();
            });

            $timeout($scope.updateExpanded, 0);
            $timeout($scope.setDefaultShortened, 0);
        }],
    };
});
