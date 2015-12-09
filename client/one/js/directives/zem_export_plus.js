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
        controller: ['$scope', '$modal', function($scope, $modal) {
            $scope.exportModalTypes = [{
                name: 'Download',
                value: 'download'
            }, {
              name: 'Schedule',
              value: 'schedule'
            }];

            $scope.showScheduledReportModal = function (exportModalType) {
                $scope.exportModalType = exportModalType;
                var modalInstance = $modal.open({
                    templateUrl: '/partials/add_scheduled_report_modal.html',
                    controller: 'AddScheduledReportModalCtrl',
                    windowClass: 'modal',
                    scope: $scope
                });
                return modalInstance;
            };
        }]
    };
});
