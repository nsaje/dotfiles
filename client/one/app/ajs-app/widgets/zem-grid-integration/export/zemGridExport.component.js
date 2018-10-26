angular.module('one.widgets').component('zemGridExport', {
    bindings: {
        api: '=',
    },
    template: require('./zemGridExport.component.html'),
    controller: function($scope, $uibModal, zemGridExportOptions) {
        var $ctrl = this;

        $ctrl.showScheduledReportModal = showScheduledReportModal;
        $ctrl.exportModalTypes = [
            {name: 'Download', value: 'download'},
            {name: 'Schedule', value: 'schedule'},
        ];

        $ctrl.$onInit = function() {
            // Workaround: for now we are relaying on legacy modals, therefor we
            // need to match API (values mostly expected on $scope)
            // TODO: Refactor Modals - will be part of tasks planned after releasing zem-grid
            var metaData = $ctrl.api.getMetaData();
            $scope.level = metaData.level;
            $scope.baseUrl = zemGridExportOptions.getBaseUrl(
                metaData.level,
                metaData.breakdown,
                metaData.id
            );
            $scope.options = zemGridExportOptions.getOptions(
                metaData.level,
                metaData.breakdown
            );
            $scope.defaultOption = zemGridExportOptions.getDefaultOption(
                $scope.options
            );
            $scope.exportSources =
                metaData.breakdown === constants.breakdown.MEDIA_SOURCE;

            $scope.getAdditionalColumns = getAdditionalColumns;
            $scope.hasPermission = $ctrl.api.hasPermission;
            $scope.isPermissionInternal = $ctrl.api.isPermissionInternal;

            if (
                $ctrl.api.hasPermission('zemauth.can_see_new_report_download')
            ) {
                $ctrl.exportModalTypes[0].name = 'Export';
            }
        };

        function initializeData() {
            $scope.order = $ctrl.api.getOrder();
        }

        function getAdditionalColumns() {
            var fields = [];
            $ctrl.api.getVisibleColumns().forEach(function(column) {
                if (column.data && !column.permanent) {
                    fields.push(column.data.field);
                }
            });
            return fields;
        }

        function showScheduledReportModal(exportModalType) {
            // Initialize data (date range, order) before modal is opened
            initializeData();

            if (exportModalType === 'schedule') {
                $uibModal.open({
                    template: require('./modals/zemAddScheduledReportModal.partial.html'), // eslint-disable-line max-len
                    controller: 'zemAddScheduledReportModalCtrl',
                    backdrop: 'static',
                    keyboard: false,
                    scope: $scope,
                });
            } else if (
                $ctrl.api.hasPermission('zemauth.can_see_new_report_download')
            ) {
                $uibModal.open({
                    component: 'zemReportDownload',
                    windowClass: 'zem-report-download',
                    backdrop: 'static',
                    resolve: {
                        api: $ctrl.api,
                    },
                });
            } else {
                $uibModal.open({
                    template: require('./modals/zemDownloadExportReportModal.partial.html'), // eslint-disable-line max-len
                    controller: 'zemDownloadExportReportModalCtrl',
                    backdrop: 'static',
                    keyboard: false,
                    scope: $scope,
                });
            }
        }
    },
});
