/* globals oneApp */
'use strict';

oneApp.directive('zemGridExport', function () {
    return {
        restrict: 'E',
        controllerAs: 'ctrl',
        scope: {},
        bindToController: {
            api: '=api',
            hasPermission: '=zemHasPermission',
            isPermissionInternal: '=zemIsPermissionInternal',
        },
        templateUrl: '/components/zem-grid-export/zem_grid_export.html',
        controller: ['$scope', '$modal', 'zemGridExportOptions', function ($scope, $modal, zemGridExportOptions) {
            var vm = this;

            vm.exportModalTypes = [
                {name: 'Download', value: 'download'},
                {name: 'Schedule', value: 'schedule'},
            ];

            vm.showScheduledReportModal = showScheduledReportModal;

            initialize();

            function initialize () {
                var metaData = vm.api.getMetaData();
                $scope.level = metaData.level;
                $scope.baseUrl = zemGridExportOptions.getBaseUrl(metaData.level, metaData.id);
                $scope.options = zemGridExportOptions.getOptions(metaData.level, metaData.breakdown);
                $scope.defaultOption = zemGridExportOptions.getDefaultOption($scope.options);

                var dataService = vm.api.getDataService();
                var dateRange = dataService.getDateRange();
                $scope.startDate = dateRange.startDate;
                $scope.endDate = dateRange.endDate;
                $scope.order = dataService.getOrder();
                $scope.exportSources = false; // FIXME

                $scope.getAdditionalColumns = getAdditionalColumns;
                $scope.hasPermission = vm.hasPermission;
                $scope.isPermissionInternal = vm.isPermissionInternal;
            }

            function getAdditionalColumns () {
                var fields = [];
                vm.api.getVisibleColumns().forEach(function (column) {
                    if (!column.unselectable)
                        fields.push(column);
                });
                return fields;
            }

            function showScheduledReportModal (exportModalType) {
                var modalInstance;
                if (exportModalType === 'schedule') {
                    modalInstance = $modal.open({
                        templateUrl: '/partials/add_scheduled_report_modal.html',
                        controller: 'AddScheduledReportModalCtrl',
                        windowClass: 'modal-default',
                        scope: $scope,
                    });
                } else {
                    modalInstance = $modal.open({
                        templateUrl: '/partials/download_export_report_modal.html',
                        controller: 'DownloadExportReportModalCtrl',
                        windowClass: 'modal-default',
                        scope: $scope,
                    });
                }
                return modalInstance;
            }
        }],
    };
});
