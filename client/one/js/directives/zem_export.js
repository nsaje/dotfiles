'use strict';

oneApp.directive('zemExport', function () {
    return {
        restrict: 'E',
        scope: {
            disabledOptions: '=',
            baseUrl: '=',
            startDate: '=',
            endDate: '=',
            options: '='
        },
        templateUrl: '/partials/zem_export.html',
        controller: ['$scope', '$window', '$compile', 'zemFilterService', function ($scope, $window, $compile, zemFilterService) {
            $scope.exportType = '';

            function getOptionByValue (value) {
                var option = null;
                $scope.options.forEach(function (opt) {
                    if (opt.value === value) {
                        option = opt;
                    }
                });

                return option;
            }

            $scope.config = {
                minimumResultsForSearch: -1,
                formatResult: function (object) {
                    if (!object.disabled) {
                        return angular.element(document.createElement('span')).text(object.text);
                    }

                    var popoverEl = angular.element(document.createElement('div'));
                    var option = getOptionByValue(object.id);

                    var popoverText = 'There is too much data to export.';
                    if (option.maxDays) {
                        popoverText += ' Please choose a smaller date range (' + option.maxDays;
                        if (option.maxDays > 1) {
                            popoverText += ' days or less).';
                        } else {
                            popoverText += ' day).';
                        }
                    } else {
                        popoverText = 'This report is not available for download, due to the volume of content indexed in this campaign. Please contact your account manager for assistance.';
                    }

                    popoverEl.attr('popover', popoverText);
                    popoverEl.attr('popover-trigger', 'mouseenter');
                    popoverEl.attr('popover-placement', 'right');
                    popoverEl.attr('popover-append-to-body', 'true');
                    popoverEl.text(object.text);

                    return $compile(popoverEl)($scope);
                },
                sortResults: function (results) {
                    var option = null;

                    // used to set disabled property on results
                    results = results.map(function (result) {
                        option = getOptionByValue(result.id);

                        if (option.disabled) {
                            result.disabled = true;
                        }
                        return result;
                    });

                    return results;
                },
                width: '12em'
            };

            $scope.downloadReport = function () {
                var url = $scope.baseUrl + 'export/?type=' + $scope.exportType + '&start_date=' + $scope.startDate.format() + '&end_date=' + $scope.endDate.format();

                if (zemFilterService.isSourceFilterOn()) {
                    url += '&filtered_sources=' + zemFilterService.getFilteredSources().join(',');
                }

                $window.open(url, '_blank');

                $scope.exportType = '';
            };
        }]
    };
});
