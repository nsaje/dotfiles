angular.module('one.widgets').component('zemReportDownload', {
    bindings: {
        close: '&',
        resolve: '<',
    },
    templateUrl: '/app/widgets/zem-report/zemReportDownload.component.html',
    controller: function (zemReportService, zemPermissions, zemUserService, zemDataFilterService, zemFilterSelectorService) {  // eslint-disable-line max-len
        var $ctrl = this;

        // Public API
        $ctrl.startReport = startReport;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;
        $ctrl.showAllSelectedFields = showAllSelectedFields;
        $ctrl.showAllAppliedFilters = showAllAppliedFilters;

        // template variables
        $ctrl.includeTotals = false;
        $ctrl.includeIds = false;
        $ctrl.includeItemsWithNoSpend = false;
        $ctrl.showIncludeItemsWithNoSpend = true;
        $ctrl.recipients = '';
        $ctrl.user = undefined;

        $ctrl.selectedFields = [];
        $ctrl.shownSelectedFields = [];

        $ctrl.jobPostingInProgress = false;
        $ctrl.jobPosted = false;

        $ctrl.$onInit = function () {
            $ctrl.user = zemUserService.current();
            $ctrl.dateRange = zemDataFilterService.getDateRange();

            $ctrl.appliedFilterConditions = zemFilterSelectorService.getAppliedConditions();

            var nrShortlistItems = 9;
            $ctrl.shownAppliedFilterConditions = $ctrl.appliedFilterConditions.slice(0, nrShortlistItems);

            $ctrl.selectedFields = getSelectedFields();
            $ctrl.shownSelectedFields = $ctrl.selectedFields.slice(0, nrShortlistItems);

            $ctrl.breakdown = $ctrl.resolve.api.getBreakdown();
            $ctrl.view = $ctrl.breakdown[0].report_query;
            if ($ctrl.view === 'Publisher') {
                $ctrl.showIncludeItemsWithNoSpend = false;
            }
            $ctrl.breakdown = $ctrl.breakdown.slice(1, $ctrl.breakdown.length);
        };

        function startReport () {
            $ctrl.jobPostingInProgress = true;
            $ctrl.errors = undefined;
            zemReportService
                .startReport($ctrl.resolve.api, $ctrl.selectedFields, {
                    includeTotals: $ctrl.includeTotals,
                    includeIds: $ctrl.includeIds,
                    includeItemsWithNoSpend: $ctrl.includeItemsWithNoSpend,
                    recipients: getRecipientsList(),
                })
                .then(function () {
                    $ctrl.jobPosted = true;
                })
                .catch(function (data) {
                    $ctrl.jobPosted = false;
                    $ctrl.errors = data.data;
                })
                .finally(function () {
                    $ctrl.jobPostingInProgress = false;
                });
        }

        function getSelectedFields () {
            var hiddenTypes = ['stateSelector', 'submissionStatus'];
            var remappedFields = {
                'Thumbnail': ['Image Hash', 'Image URL'],
            };
            var alwaysFields = {
                'ad_groups': ['Account', 'Campaign', 'Ad Group'],
                'campaigns': ['Account', 'Campaign'],
                'accounts': ['Account'],
                'all_accounts': [],
            };

            var fields = alwaysFields[$ctrl.resolve.api.getMetaData().level];
            if ($ctrl.hasPermission('zemauth.can_view_account_agency_information') &&
                    fields.indexOf('Account') >= 0) {
                fields.unshift('Agency');
            }

            var breakdown = $ctrl.resolve.api.getBreakdown();
            for (var i = 0; i < breakdown.length; i++) {
                fields.push(breakdown[i].report_query);
            }

            var columns = $ctrl.resolve.api.getColumns();
            for (i = 0; i < columns.length; i++) {
                if (columns[i].visible &&
                        !columns[i].disabled &&
                        columns[i].data.name &&
                        hiddenTypes.indexOf(columns[i].data.type) < 0 &&
                        fields.indexOf(columns[i].data.name) < 0) {
                    if (columns[i].data.name in remappedFields) {
                        fields = fields.concat(remappedFields[columns[i].data.name]);
                    } else {
                        fields.push(columns[i].data.name);
                    }
                }
            }

            return fields;
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
