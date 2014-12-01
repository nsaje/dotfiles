"use strict";

oneApp.directive('zemExport', function() {
    return {
        restrict: 'E',
        scope: {
            disabledOptions: '@',
            baseUrl: '=',
            startDate: '=',
            endDate: '='
        },
        templateUrl: '/partials/zem_export.html',
        controller: ['$scope', '$window', '$compile', function($scope, $window, $compile) {
            $scope.exportType = '';

            $scope.config = {
                minimumResultsForSearch: -1,
                formatResult: function (object) {
                    if (!object.disabled) {
                        return angular.element(document.createElement('span')).text(object.text);
                    }

                    var popoverEl = angular.element(document.createElement('div'));

                    popoverEl.attr('popover', 'There is too much data to export. Please choose a smaller date range.');
                    popoverEl.attr('popover-trigger', 'mouseenter');
                    popoverEl.attr('popover-placement', 'right');
                    popoverEl.attr('popover-append-to-body', 'true');
                    popoverEl.text(object.text);

                    return $compile(popoverEl)($scope);
                },
                sortResults: function (results) {
                    // used to set disabled property on results
                    if ($scope.disabledOptions) {
                        results = results.map(function (result) {
                            if ($scope.disabledOptions.indexOf(result.id) !== -1) {
                                result.disabled = true;
                            }
                            return result;
                        });
                    }

                    return results;
                }
            };

            $scope.downloadReport = function() {
                $window.open($scope.baseUrl + 'export/?type=' + $scope.exportType + '&start_date=' + $scope.startDate.format() + '&end_date=' + $scope.endDate.format(), '_blank');

                $scope.exportType = '';
            };
        }]
    }
});
