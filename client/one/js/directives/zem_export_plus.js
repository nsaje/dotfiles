/*globals oneApp,constants*/
"use strict";

oneApp.directive('zemExportPlus', function() {
    return {
        restrict: 'E',
        scope: {
            baseUrl: '=',
            startDate: '=',
            endDate: '=',
            options: '=',
            columns: '=',
            order: '=',
            level: '=',
            exportSources: '='
        },
        templateUrl: '/partials/zem_export_plus.html',
        controller: ['$scope', '$window', '$compile', 'zemFilterService', 'api', '$state', function($scope, $window, $compile, zemFilterService, api, $state) {

            $scope.setDisabledExportOptions = function() {
                api.exportPlusAllowed.get($state.params.id, $scope.level, $scope.exportSources).then(
                    function (data) {
                        $scope.options.forEach(function (opt) {
                            if (opt.value === constants.exportType.VIEW) {
                                opt.disabled = !data.view;
                            } else if (opt.value === constants.exportType.CONTENT_AD) {
                                opt.disabled = !data.content_ad;
                            } else if (opt.value === constants.exportType.AD_GROUP) {
                                opt.disabled = !data.ad_group;
                            } else if (opt.value === constants.exportType.CAMPAIGN) {
                                opt.disabled = !data.campaign;
                            } else if (opt.value === constants.exportType.ACCOUNT) {
                                opt.disabled = !data.account;
                            }
                        });
                    }
                 );
            };

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
            };

            $scope.setDisabledExportOptions();
        }]
    };
});
