/* globals oneApp */
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
        controller: ['$scope', '$element', '$window', function ($scope, $element, $window) {
            $scope.expanded = true;

            var w = angular.element($window);
            $scope.$watch(function () {
                return {
                    'h': w.height(), 
                    'w': w.width()
                };
            }, function (newValue, oldValue) {
                var containerWidth = $('.insights-container').width();
                if (containerWidth < 800) {
                    $scope.expanded = false;
                } else {
                    $scope.expanded = true;
                    $scope.setDefaultShortened();
                }
            }, true);

            w.bind('resize', function () {
               $scope.$apply();
            });

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

            $scope.setDefaultShortened();
        }],
    };
});
