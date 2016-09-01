/* globals oneApp, constants */
'use strict';

oneApp.directive('zemGridExport', function () {
    return {
        restrict: 'E',
        controllerAs: 'ctrl',
        scope: {},
        bindToController: {
            api: '=api',
        },
        templateUrl: '/components/zem-grid-integration/shared/zem-grid-export/zemGridExport.component.html',
        controller: 'zemGridExportCtrl',
    };
});


oneApp.controller('zemGridExportCtrl', ['$scope', '$uibModal', 'zemGridExportOptions', function ($scope, $uibModal, zemGridExportOptions) {
    var vm = this;

    vm.showScheduledReportModal = showScheduledReportModal;
    vm.exportModalTypes = [
        {name: 'Download', value: 'download'},
        {name: 'Schedule', value: 'schedule'},
    ];

    initialize();

    function initialize () {
        // Workaround: for now we are relaying on legacy modals, therefor we
        // need to match API (values mostly expected on $scope)
        // TODO: Refactor Modals - will be part of tasks planned after releasing zem-grid
        var metaData = vm.api.getMetaData();
        $scope.level = metaData.level;
        $scope.baseUrl = zemGridExportOptions.getBaseUrl(metaData.level, metaData.breakdown, metaData.id);
        $scope.options = zemGridExportOptions.getOptions(metaData.level, metaData.breakdown);
        $scope.defaultOption = zemGridExportOptions.getDefaultOption($scope.options);
        $scope.exportSources = metaData.breakdown === constants.breakdown.MEDIA_SOURCE;

        $scope.getAdditionalColumns = getAdditionalColumns;
        $scope.hasPermission = vm.api.hasPermission;
        $scope.isPermissionInternal = vm.api.isPermissionInternal;
    }

    function initializeData () {
        $scope.dateRange = vm.api.getDateRange();
        $scope.order = vm.api.getOrder();
    }

    function getAdditionalColumns () {
        var fields = [];
        vm.api.getVisibleColumns().forEach(function (column) {
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
                windowClass: 'modal-default',
                scope: $scope,
            });
        } else {
            modalInstance = $uibModal.open({
                templateUrl: '/partials/download_export_report_modal.html',
                controller: 'DownloadExportReportModalCtrl',
                windowClass: 'modal-default',
                scope: $scope,
            });
        }
        return modalInstance;
    }
}]);
