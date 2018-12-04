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
        zemCostModeService,
        zemPermissions
    ) {
        var $ctrl = this;

        var HIDDEN_TYPES = ['stateSelector', 'submissionStatus'];

        var NR_SHORTLIST_ITEMS = 9;
        var SHORTLIST_LIMIT = 15;
        var refundColumns = [];
        var allColumns = [];

        //
        // Public API
        //
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;
        $ctrl.onColumnToggled = onColumnToggled;
        $ctrl.onAllColumnsToggled = onAllColumnsToggled;

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

        $ctrl.categories = [];
        $ctrl.selectedColumns = [];

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

            allColumns = getAllColumns();
            refundColumns = getRefundColumns(allColumns);
            $ctrl.categories = getCategories(allColumns);
            $ctrl.selectedColumns = getSelectedColumns();

            update();
        };

        function onColumnToggled(field) {
            var column =
                $ctrl.gridApi.findColumnInCategories($ctrl.categories, field) ||
                {};
            setVisibleColumns(column, !column.visible);
        }

        function onAllColumnsToggled(isChecked) {
            setVisibleColumns(
                $ctrl.gridApi.getTogglableColumns(allColumns),
                isChecked
            );
        }

        function setVisibleColumns(toggledColumns, visible) {
            var columnsToToggle = $ctrl.gridApi.getColumnsToToggle(
                toggledColumns,
                allColumns
            );

            columnsToToggle.forEach(function(column) {
                column.visible = visible;
            });

            $ctrl.categories = getCategories(allColumns);

            toggleColumns(columnsToToggle.map(getColumnName), visible);
        }

        function toggleColumns(columnsToToggle, visible) {
            columnsToToggle.forEach(function(column) {
                var index;
                if (visible) {
                    index = $ctrl.selectedColumns.indexOf(column);
                    if (index === -1) {
                        $ctrl.selectedColumns.push(column);
                    }
                } else {
                    index = $ctrl.selectedColumns.indexOf(column);
                    if (index !== -1) {
                        $ctrl.selectedColumns.splice(index, 1);
                    }
                }
            });

            $ctrl.update();
        }

        function update() {
            var fields = zemReportFieldsService.getFields(
                $ctrl.gridApi.getMetaData().level,
                $ctrl.gridApi.getMetaData().breakdown,
                $ctrl.breakdown,
                $ctrl.config.includeIds,
                $ctrl.selectedColumns,
                getTogglableColumns(allColumns),
                getGridColumns(allColumns)
            );

            handleRefunds(fields);
            $ctrl.config.selectedFields = fields;

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

        function getAllColumns() {
            return angular.copy($ctrl.gridApi.getColumns());
        }

        function getRefundColumns(columns) {
            var refundColumns = [];
            for (var i = 0; i < columns.length; i++) {
                if (columns[i].data.isRefund) {
                    refundColumns.push(getColumnName(columns[i]));
                }
            }
            return refundColumns;
        }

        function getCategories(columns) {
            return $ctrl.gridApi.getCategorizedColumns(
                zemCostModeService,
                columns
            );
        }

        function getSelectedColumns() {
            var selectedColumns = [];
            $ctrl.categories.forEach(function(category) {
                selectedColumns = selectedColumns.concat(
                    category.columns.filter(function(item) {
                        return item.visible;
                    })
                );
            });
            return selectedColumns.map(getColumnName);
        }

        function getTogglableColumns(columns) {
            return $ctrl.gridApi
                .getTogglableColumns(columns)
                .map(getColumnName);
        }

        function getGridColumns(columns) {
            var gridColumns = [];
            for (var i = 0; i < columns.length; i++) {
                if (
                    columns[i].visible &&
                    !columns[i].disabled &&
                    columns[i].data.name &&
                    HIDDEN_TYPES.indexOf(columns[i].data.type) < 0
                ) {
                    gridColumns.push(getColumnName(columns[i]));
                }
            }
            return gridColumns;
        }

        function addBreakdown(breakdown) {
            $ctrl.breakdown.push(breakdown);
            update();
        }

        function removeBreakdown(breakdown) {
            $ctrl.breakdown.splice($ctrl.breakdown.indexOf(breakdown), 1);
            update();
        }

        function handleRefunds(fields) {
            if ($ctrl.config.allAccountsIncludeCreditRefunds) {
                includeRefundColumns(fields);
            } else {
                removeRefundColumns(fields);
            }
        }

        function includeRefundColumns(fields) {
            refundColumns
                .filter(function(col) {
                    var costCol = col.replace(/ Refund$/, '');
                    return fields.indexOf(costCol) >= 0;
                })
                .forEach(function(col) {
                    var colIndex = fields.indexOf(col);
                    if (colIndex === -1) {
                        var costCol = col.replace(/ Refund$/, '');
                        var costColIndex = fields.indexOf(costCol);
                        fields.splice(costColIndex + 1, 0, col);
                    }
                });
        }

        function removeRefundColumns(fields) {
            refundColumns.forEach(function(col) {
                var colIndex = fields.indexOf(col);
                if (colIndex > -1) {
                    fields.splice(colIndex, 1);
                }
            });
        }

        function showAllSelectedFields() {
            $ctrl.shownSelectedFields = $ctrl.config.selectedFields;
        }

        function showAllAppliedFilters() {
            $ctrl.shownAppliedFilterConditions = $ctrl.appliedFilterConditions;
        }

        function getColumnName(column) {
            return column.data.name;
        }
    },
});
