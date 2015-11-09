"use strict";

oneApp.directive('zemExportPlus', function() {
    return {
        restrict: 'E',
        scope: {
            disabledOptions: '=',
            baseUrl: '=',
            startDate: '=',
            endDate: '=',
            options: '=',
            columns: '=',
            order: '='
        },
        templateUrl: '/partials/zem_export_plus.html',
        controller: ['$scope', '$window', '$compile', 'zemFilterService', function($scope, $window, $compile, zemFilterService) {
            $scope.exportType = '';

            $scope.downloadReport = function(exportType) {

                var url = $scope.baseUrl + 'export_plus/?type=' + exportType +
                          '&start_date=' + $scope.startDate.format() +
                          '&end_date=' + $scope.endDate.format() +
                          '&order=' + $scope.order;

                if (zemFilterService.isSourceFilterOn()) {
                    url += '&filtered_sources=' + zemFilterService.getFilteredSources().join(',');
                }

                var exportColumns = [];
                for (var i = 0; i < $scope.columns.length; i++) {
                  var col = $scope.columns[i];
                  if (col.shown && col.checked && !col.unselectable){
                    exportColumns.push(col.field);
                  }
                }
                url += '&additional_fields=' + exportColumns.join(',');

                $window.open(url, '_blank');

                $scope.exportType = '';
            };
        }]
    };
});
