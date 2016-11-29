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

        $ctrl.selectedFields = [];

        $ctrl.jobPostingInProgress = false;
        $ctrl.jobPosted = false;
        $ctrl.jobPostedSuccessfully = false;

        $ctrl.$onInit = function () {
            $ctrl.user = zemUserService.current();
            $ctrl.dateRange = zemDataFilterService.getDateRange();
            $ctrl.appliedFilterConditions = zemFilterSelectorService.getAppliedConditions();
            $ctrl.selectedFields = getSelectedFields();
        };

        function startReport () {
            $ctrl.jobPostingInProgress = true;
            zemReportService
                .startReport($ctrl.resolve.api, $ctrl.selectedFields, {
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

        function getSelectedFields () {

            var fields = [], columns = $ctrl.resolve.api.getColumns();

            var breakdown = $ctrl.resolve.api.getBreakdown();
            for (var i = 0; i < breakdown.length; i++) {
                fields.push(breakdown[i].report_query);
            }

            for (i = 0; i < columns.length; i++) {
                if (columns[i].visible && columns[i].data.name && fields.indexOf(columns[i].data.name) < 0) {
                    fields.push(columns[i].data.name);
                }
            }

            return fields;
        }
    }
});