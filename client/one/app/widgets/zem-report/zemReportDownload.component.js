angular.module('one.widgets').component('zemReportDownload', {
    bindings: {
        close: '&',
        resolve: '<',
    },
    templateUrl: '/app/widgets/zem-report/zemReportDownload.component.html',
    controller: function ($interval, zemReportService, zemReportBreakdownService, zemReportFieldsService, zemPermissions, zemUserService, zemDataFilterService, zemFilterSelectorService) {  // eslint-disable-line max-len
        var $ctrl = this;

        var NR_SHORTLIST_ITEMS = 9;
        var SHORTLIST_LIMIT = 15;

        // Public API
        $ctrl.startReport = startReport;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;
        $ctrl.showAllSelectedFields = showAllSelectedFields;
        $ctrl.showAllAppliedFilters = showAllAppliedFilters;
        $ctrl.addBreakdown = addBreakdown;
        $ctrl.update = update;
        $ctrl.cancel = cancel;

        // template variables
        $ctrl.includeTotals = false;
        $ctrl.includeIds = false;
        $ctrl.includeItemsWithNoSpend = false;
        $ctrl.showIncludeItemsWithNoSpend = true;
        $ctrl.sendReport = false;
        $ctrl.recipients = '';
        $ctrl.user = undefined;

        $ctrl.selectedFields = [];
        $ctrl.shownSelectedFields = [];

        $ctrl.jobPosted = false;
        $ctrl.jobDone = false;
        $ctrl.reportSent = false;
        $ctrl.pollInterval = null;

        $ctrl.availableBreakdowns = {};

        $ctrl.$onInit = function () {
            $ctrl.user = zemUserService.current();
            $ctrl.dateRange = zemDataFilterService.getDateRange();

            $ctrl.appliedFilterConditions = zemFilterSelectorService.getAppliedConditions();
            if ($ctrl.appliedFilterConditions.length > SHORTLIST_LIMIT) {
                $ctrl.shownAppliedFilterConditions = $ctrl.appliedFilterConditions.slice(0, NR_SHORTLIST_ITEMS);
            }

            $ctrl.breakdown = angular.copy($ctrl.resolve.api.getBreakdown());

            $ctrl.view = $ctrl.breakdown[0].report_query;
            if ($ctrl.view === 'Publisher') {
                $ctrl.showIncludeItemsWithNoSpend = false;
            }

            update();
        };

        function addBreakdown (breakdown) {
            $ctrl.breakdown.push(breakdown);
            update();
        }

        function cancel () {
            stopPolling();
            $ctrl.close();
        }

        function update () {
            $ctrl.selectedFields = zemReportFieldsService.getFields(
                $ctrl.resolve.api,
                $ctrl.breakdown,
                $ctrl.includeIds
            );
            if ($ctrl.shownSelectedFields.length <= NR_SHORTLIST_ITEMS &&
                    $ctrl.selectedFields.length > SHORTLIST_LIMIT) {
                $ctrl.shownSelectedFields = $ctrl.selectedFields.slice(0, NR_SHORTLIST_ITEMS);
            } else {
                $ctrl.showAllSelectedFields();
            }

            $ctrl.shownBreakdown = $ctrl.breakdown.slice(1, $ctrl.breakdown.length);

            $ctrl.availableBreakdowns = zemReportBreakdownService.getAvailableBreakdowns(
                $ctrl.breakdown,
                $ctrl.resolve.api.getMetaData()
            );
        }

        function startPolling (id) {
            if ($ctrl.pollInterval !== null) {
                return;
            }

            $ctrl.pollInterval = $interval(function () {
                zemReportService
                    .getReport(id)
                    .then(function (data) {
                        if (data.data.status === 'IN_PROGRESS') {
                            return;
                        }

                        if (data.data.status === 'FAILED') {
                            $ctrl.jobDone = true;
                            $ctrl.hasError = true;
                        } else if (data.data.status === 'DONE') {
                            $ctrl.jobDone = true;
                            $ctrl.reportUrl = data.data.result;
                        }
                        stopPolling();
                    })
                    .catch(function (data) {
                        $ctrl.jobDone = true;
                        $ctrl.hasError = true;
                        if (data) {
                            $ctrl.errors = data.data;
                        }
                        stopPolling();
                    });
            }, 2500);
        }

        function stopPolling () {
            if ($ctrl.pollInterval !== null) {
                $interval.cancel($ctrl.pollInterval);
                $ctrl.pollInterval = null;
            }
        }

        function startReport () {
            $ctrl.jobPosted = true;
            $ctrl.errors = undefined;
            zemReportService
                .startReport($ctrl.resolve.api, $ctrl.selectedFields, {
                    includeTotals: $ctrl.includeTotals,
                    includeIds: $ctrl.includeIds,
                    includeItemsWithNoSpend: $ctrl.includeItemsWithNoSpend,
                    sendReport: $ctrl.sendReport,
                    recipients: getRecipientsList(),
                })
                .then(function (data) {
                    if ($ctrl.sendReport) {
                        $ctrl.jobDone = true;
                        $ctrl.reportSent = true;
                    } else {
                        startPolling(data.data.id);
                    }
                })
                .catch(function (data) {
                    $ctrl.jobDone = true;
                    $ctrl.hasError = true;
                    $ctrl.errors = data;
                });
        }

        function showAllSelectedFields () {
            $ctrl.shownSelectedFields = $ctrl.selectedFields;
        }

        function showAllAppliedFilters () {
            $ctrl.shownAppliedFilterConditions = $ctrl.appliedFilterConditions;
        }

        function getRecipientsList () {
            var recipients = [], list = $ctrl.recipients.split(',');
            for (var i = 0; i < list.length; i++) {
                if (list[i] && list[i].trim()) {
                    recipients.push(list[i]);
                }
            }
            return recipients;
        }
    }
});
