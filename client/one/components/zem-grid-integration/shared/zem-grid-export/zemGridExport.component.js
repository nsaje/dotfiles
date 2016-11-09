/* globals angular, constants */

angular.module('one.legacy').component('zemGridExport', {
    bindings: {
        api: '=',
    },
    templateUrl: '/components/zem-grid-integration/shared/zem-grid-export/zemGridExport.component.html',
    controller: function ($scope, $uibModal, zemGridExportOptions) {
        var $ctrl = this;

        $ctrl.showScheduledReportModal = showScheduledReportModal;
        $ctrl.exportModalTypes = [
            {name: 'Download', value: 'download'},
            {name: 'Schedule', value: 'schedule'},
        ];

        $ctrl.$onInit = function () {
            // Workaround: for now we are relaying on legacy modals, therefor we
            // need to match API (values mostly expected on $scope)
            // TODO: Refactor Modals - will be part of tasks planned after releasing zem-grid
            var metaData = $ctrl.api.getMetaData();
            $scope.level = metaData.level;
            $scope.baseUrl = zemGridExportOptions.getBaseUrl(metaData.level, metaData.breakdown, metaData.id);
            $scope.options = zemGridExportOptions.getOptions(metaData.level, metaData.breakdown);
            $scope.defaultOption = zemGridExportOptions.getDefaultOption($scope.options);
            $scope.exportSources = metaData.breakdown === constants.breakdown.MEDIA_SOURCE;

            $scope.getAdditionalColumns = getAdditionalColumns;
            $scope.hasPermission = $ctrl.api.hasPermission;
            $scope.isPermissionInternal = $ctrl.api.isPermissionInternal;
        };

        function initializeData () {
            $scope.order = $ctrl.api.getOrder();
        }

        function getAdditionalColumns () {
            var fields = [];
            $ctrl.api.getVisibleColumns().forEach(function (column) {
                if (column.data && !column.permanent) {
                    fields.push(column.data.field);
                }
            });
            return fields;
        }

        function showScheduledReportModal (exportModalType) {
            // Initialize data (date range, order) before modal is opened
            initializeData();

            var modalInstance;
            if (exportModalType === 'schedule') {
                modalInstance = $uibModal.open({
                    templateUrl: '/partials/add_scheduled_report_modal.html',
                    controller: 'AddScheduledReportModalCtrl',
                    backdrop: 'static',
                    keyboard: false,
                    scope: $scope,
                });
            } else {
                modalInstance = $uibModal.open({
                    templateUrl: '/partials/download_export_report_modal.html',
                    controller: 'DownloadExportReportModalCtrl',
                    backdrop: 'static',
                    keyboard: false,
                    scope: $scope,
                });
                return modalInstance;
            }
        }
    }
});
