angular.module('one.widgets').component('zemReportDownload', {
    bindings: {
        close: '&',
        resolve: '=',  // TODO is ok 2 way binding?
    },
    templateUrl: '/app/widgets/zem-report/zemReportDownload.component.html',
    controller: ['zemReportService', 'zemPermissions', 'zemUserService', function (zemReportService, zemPermissions, zemUserService) { // eslint-disable-line max-len
        var $ctrl = this;

        // Public API
        $ctrl.startReport = startReport;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        // template variables
        $ctrl.includeTotals = false;
        $ctrl.includeIds = false;
        $ctrl.includeMissing = false;
        $ctrl.user = undefined;

        $ctrl.$onInit = function () {
            $ctrl.user = zemUserService.current();
        };

        function startReport () {
            zemReportService
                .startReport($ctrl.resolve.api, {
                    includeTotals: $ctrl.includeTotals,
                    includeIds: $ctrl.includeIds,
                    includeMissing: $ctrl.includeMissing,
                })
                .then(function () {
                    console.log('Start report succeeded');  // eslint-disable-line no-console
                })
                .catch(function () {
                    console.log('Start report failed');  // eslint-disable-line no-console
                });
        }
    }]
});