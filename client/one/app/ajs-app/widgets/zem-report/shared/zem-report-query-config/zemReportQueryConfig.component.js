require('./zemReportQueryConfig.component.less');

angular.module('one.widgets').component('zemReportQueryConfig', {
    bindings: {
        gridApi: '<',
        disabled: '<',
        config: '=',
    },
    template: require('./zemReportQueryConfig.component.html'),
    controller: function(
        zemFilterSelectorService,
        zemReportBreakdownService,
        zemReportFieldsService,
        zemPermissions
    ) {
        var $ctrl = this;

        var NR_SHORTLIST_ITEMS = 9;
        var SHORTLIST_LIMIT = 15;
        var refundColumns = [
            'Media Spend Refund',
            'License Fee Refund',
            'Total Spend Refund',
        ];

        //
        // Public API
        //
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.showAllSelectedFields = showAllSelectedFields;
        $ctrl.showAllAppliedFilters = showAllAppliedFilters;
        $ctrl.addBreakdown = addBreakdown;
        $ctrl.removeBreakdown = removeBreakdown;
        $ctrl.update = update;
        $ctrl.toggleColumns = toggleColumns;

        // template variables
        $ctrl.config = {
            includeTotals: false,
            includeIds: false,
            includeItemsWithNoSpend: false,
            allAccountsInLocalCurrency: false,
            allAccountsIncludeCreditRefunds: false,
            selectedFields: [],
        };
        $ctrl.showTruncatedColsList = true;
        $ctrl.showIncludeItemsWithNoSpend = true;
        $ctrl.showAllAccountsInLocalCurrencyCheckbox = false;
        $ctrl.showAllAccountsCreditRefunds = false;
        $ctrl.shownSelectedFields = [];
        $ctrl.appliedFilterConditions = [];
        $ctrl.view = '';
        $ctrl.breakdown = [];
        $ctrl.availableBreakdowns = {};
        $ctrl.selectedColumns = [];
        $ctrl.unselectedColumns = [];

        $ctrl.$onInit = function() {
            $ctrl.appliedFilterConditions = zemFilterSelectorService.getAppliedConditions();
            if ($ctrl.appliedFilterConditions.length > SHORTLIST_LIMIT) {
                $ctrl.shownAppliedFilterConditions = $ctrl.appliedFilterConditions.slice(
                    0,
                    NR_SHORTLIST_ITEMS
                );
            } else {
                $ctrl.showAllAppliedFilters();
            }

            $ctrl.breakdown = angular.copy($ctrl.gridApi.getBreakdown());

            $ctrl.view = $ctrl.breakdown[0].report_query;
            if ($ctrl.view === 'Publisher') {
                $ctrl.showIncludeItemsWithNoSpend = false;
            }

            if (
                $ctrl.view === 'Account' &&
                zemPermissions.hasPermission(
                    'zemauth.can_request_accounts_report_in_local_currencies'
                )
            ) {
                $ctrl.showAllAccountsInLocalCurrencyCheckbox = true;
            }

            if (
                $ctrl.view === 'Account' &&
                zemPermissions.hasPermission(
                    'zemauth.can_include_credit_refunds_in_report'
                )
            ) {
                $ctrl.showAllAccountsCreditRefunds = true;
            }

            update();
        };

        function addBreakdown(breakdown) {
            $ctrl.breakdown.push(breakdown);
            update();
        }

        function removeBreakdown(breakdown) {
            $ctrl.breakdown.splice($ctrl.breakdown.indexOf(breakdown), 1);
            update();
        }

        function onlyUnique(value, index, self) {
            return self.indexOf(value) === index;
        }

        function toggleColumns(columnsToToggle, visible) {
            columnsToToggle.forEach(function(column) {
                var index;
                if (visible) {
                    index = $ctrl.selectedColumns.indexOf(column);
                    if (index === -1) {
                        $ctrl.selectedColumns.push(column);
                    }
                    index = $ctrl.unselectedColumns.indexOf(column);
                    if (index !== -1) {
                        $ctrl.unselectedColumns.splice(index, 1);
                    }
                } else {
                    index = $ctrl.selectedColumns.indexOf(column);
                    if (index !== -1) {
                        $ctrl.selectedColumns.splice(index, 1);
                    }
                    index = $ctrl.unselectedColumns.indexOf(column);
                    if (index === -1) {
                        $ctrl.unselectedColumns.push(column);
                    }
                }
            });

            $ctrl.update();
        }

        function update() {
            var defaultFields = zemReportFieldsService.getFields(
                $ctrl.gridApi,
                $ctrl.breakdown,
                $ctrl.config.includeIds
            );
            var selectedFields = $ctrl.selectedColumns;
            var unSelectedFields = $ctrl.unselectedColumns;

            if ($ctrl.config.allAccountsIncludeCreditRefunds) {
                includeRefundColumns(selectedFields);
            } else {
                removeRefundColumns(selectedFields);
            }

            var mergedFields = defaultFields
                .filter(function(field) {
                    return unSelectedFields.indexOf(field) === -1;
                })
                .concat(selectedFields)
                .filter(onlyUnique);

            $ctrl.config.selectedFields = mergedFields;
            $ctrl.showAllSelectedFields();

            if (
                $ctrl.shownSelectedFields.length > SHORTLIST_LIMIT &&
                $ctrl.showTruncatedColsList
            ) {
                // user sees "..." only once. If the user interacts with column
                // selection component we display all columns
                $ctrl.showTruncatedColsList = false;
                $ctrl.shownSelectedFields = $ctrl.config.selectedFields.slice(
                    0,
                    SHORTLIST_LIMIT
                );
            }

            $ctrl.shownBreakdown = $ctrl.breakdown.slice(
                1,
                $ctrl.breakdown.length
            );

            $ctrl.availableBreakdowns = zemReportBreakdownService.getAvailableBreakdowns(
                $ctrl.breakdown,
                $ctrl.gridApi.getMetaData()
            );
        }

        function includeRefundColumns(selectedFields) {
            refundColumns.forEach(function(col) {
                var ix = selectedFields.indexOf(col);
                if (ix === -1) {
                    selectedFields.push(col);
                }
            });
        }

        function removeRefundColumns(selectedFields) {
            refundColumns.forEach(function(col) {
                var ix = selectedFields.indexOf(col);
                if (ix > -1) {
                    selectedFields.splice(ix, 1);
                }
            });
        }

        function showAllSelectedFields() {
            $ctrl.shownSelectedFields = $ctrl.config.selectedFields;
        }

        function showAllAppliedFilters() {
            $ctrl.shownAppliedFilterConditions = $ctrl.appliedFilterConditions;
        }
    },
});
