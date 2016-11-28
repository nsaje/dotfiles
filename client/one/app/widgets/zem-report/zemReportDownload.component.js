angular.module('one.widgets').component('zemReportDownload', {
    bindings: {
        close: '&',
        resolve: '=',
    },
    templateUrl: '/app/widgets/zem-report/zemReportDownload.component.html',
    controller: function (zemReportService, zemPermissions, zemUserService, zemDataFilterService, zemFilterSelectorService) {  // eslint-disable-line max-len
        var $ctrl = this;

        // Public API
        $ctrl.startReport = startReport;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        // template variables
        $ctrl.includeTotals = false;
        $ctrl.user = undefined;

        $ctrl.dateRange = zemDataFilterService.getDateRange();
        $ctrl.appliedFilterConditions = zemFilterSelectorService.getAppliedConditions();

        $ctrl.jobPostingInProgress = false;
        $ctrl.jobPosted = false;
        $ctrl.jobPostedSuccessfully = false;

        $ctrl.$onInit = function () {
            $ctrl.user = zemUserService.current();
        };

        function startReport () {
            $ctrl.jobPostingInProgress = true;
            zemReportService
                .startReport($ctrl.resolve.api, {
                    includeTotals: $ctrl.includeTotals,
                })
                .then(function () {
                    $ctrl.jobPostedSuccessfully = true;
                })
                .catch(function () {
                    $ctrl.jobPostedSuccessfully = false;
                })
                .finally(function () {
                    $ctrl.jobPosted = true;
                    $ctrl.jobPostingInProgress = false;
                });
        }
    }
});