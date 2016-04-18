/*globals oneApp,constants*/
'use strict';

oneApp.directive('zemExport', function () {
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
            exportSources: '=',
            hasPermission: '=zemHasPermission',
            isPermissionInternal: '=zemIsPermissionInternal'
        },
        templateUrl: '/partials/zem_export_plus.html',
        controller: ['$scope', '$modal', function ($scope, $modal) {
            $scope.exportModalTypes = [{
                name: 'Download',
                value: 'download'
            }, {
                name: 'Schedule',
                value: 'schedule'
            }];

            $scope.defaultOption = $scope.options[0];
            for (var i = 1; i < $scope.options.length; ++i) {
                if ($scope.options[i].defaultOption) {
                    $scope.defaultOption = $scope.options[i];
                    break;
                }
            }

            $scope.getAdditionalColumns = function () {
                var exportColumns = [];
                for (var i = 0; i < $scope.columns.length; i++) {
                    var col = $scope.columns[i];
                    if (col.shown && col.checked && !col.unselectable) {
                      exportColumns.push(col.field);
                  }
                }
                return exportColumns;
            };

            $scope.showScheduledReportModal = function (exportModalType) {
                var modalInstance;
                if (exportModalType === 'schedule') {
                    modalInstance = $modal.open({
                            templateUrl: '/partials/add_scheduled_report_modal.html',
                            controller: 'AddScheduledReportModalCtrl',
                            windowClass: 'modal',
                            scope: $scope
                        });
                } else {
                    modalInstance = $modal.open({
                            templateUrl: '/partials/download_export_report_modal.html',
                            controller: 'DownloadExportReportModalCtrl',
                            windowClass: 'modal',
                            scope: $scope
                        });
                }
                return modalInstance;
            };
        }]
    };
});
