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
        zemUserService,
        zemLocalStorageService,
        zemPermissions
    ) {
        var $ctrl = this;

        var HIDDEN_TYPES = ['stateSelector', 'submissionStatus'];

        var NR_SHORTLIST_ITEMS = 9;
        var SHORTLIST_LIMIT = 15;
        var LOCAL_STORAGE_NAMESPACE = 'zemReportQueryConfig';
        var KEY_CSV_SEPARATOR = 'csvSeparator';
        var KEY_CSV_DECIMAL_SEPARATOR = 'csvDecimalSeparator';
        var refundColumns = [];
        var allColumns = [];

        //
        // Public API
        //
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;
        $ctrl.onCsvSeparatorOtherChanged = onCsvSeparatorOtherChanged;
        $ctrl.onColumnToggled = onColumnToggled;
        $ctrl.onColumnsToggled = onColumnsToggled;
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
            includeEntityTags: false,
            csvSeparator: null,
            csvDecimalSeparator: null,
            selectedFields: [],
        };
        $ctrl.showTruncatedColsList = true;
        $ctrl.showIncludeItemsWithNoSpend = true;
        $ctrl.showAllAccountsInLocalCurrencyCheckbox = false;
        $ctrl.showAllAccountsCreditRefunds = false;
        $ctrl.showIncludeEntityTags = false;
        $ctrl.shownSelectedFields = [];
        $ctrl.appliedFilterConditions = [];
        $ctrl.view = '';
        $ctrl.breakdown = [];
        $ctrl.availableBreakdowns = {};
        $ctrl.csvSeparatorOther = '';

        $ctrl.categories = [];
        $ctrl.selectedColumns = [];

        $ctrl.$onInit = function() {
            var visibleSections = zemFilterSelectorService.getVisibleSections();
            $ctrl.appliedFilterConditions = zemFilterSelectorService.getAppliedConditions(
                visibleSections
            );
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

            if (
                zemPermissions.hasPermission(
                    'zemauth.can_include_tags_in_reports'
                )
            ) {
                $ctrl.showIncludeEntityTags = true;
            }

            allColumns = getAllColumns();
            refundColumns = getRefundColumns(allColumns);
            $ctrl.categories = getCategories(allColumns);
            $ctrl.selectedColumns = getSelectedColumns($ctrl.categories);

            initializeCsvOptions();

            update();
        };

        function initializeCsvOptions() {
            var user = zemUserService.current();
            var localCsvSeparator = zemLocalStorageService.get(
                KEY_CSV_SEPARATOR,
                LOCAL_STORAGE_NAMESPACE
            );
            var localCsvDecimalSeparator = zemLocalStorageService.get(
                KEY_CSV_DECIMAL_SEPARATOR,
                LOCAL_STORAGE_NAMESPACE
            );

            $ctrl.config.csvSeparator =
                localCsvSeparator || user.defaultCsvSeparator || ',';
            $ctrl.config.csvDecimalSeparator =
                localCsvDecimalSeparator ||
                user.defaultCsvDecimalSeparator ||
                '.';
            if (
                $ctrl.config.csvSeparator !== ',' &&
                $ctrl.config.csvSeparator !== ';' &&
                $ctrl.config.csvSeparator !== '\t'
            ) {
                $ctrl.csvSeparatorOther = $ctrl.config.csvSeparator;
            }
        }

        function onCsvSeparatorOtherChanged() {
            $ctrl.config.csvSeparator = $ctrl.csvSeparatorOther;
            update();
        }

        function onColumnToggled(field) {
            var column =
                $ctrl.gridApi.findColumnInCategories($ctrl.categories, field) ||
                {};
            setVisibleColumns(column, !column.visible);
        }

        function onColumnsToggled(fields) {
            fields.forEach(function(field) {
                $ctrl.onColumnToggled(field);
            });
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

            rememberCsvConfig();
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

        // This function is used to initialize the state of currently selected
        // columns in the grid. It uses recursion to find selected columns
        // in all categories, subcategories, subsubcategories, ...
        function getSelectedColumns(categories) {
            var selectedColumns = [];
            categories.forEach(function(category) {
                if (category.columns && category.columns.length > 0) {
                    category.columns.forEach(function(column) {
                        if (column.visible && !column.disabled) {
                            var categorySelectedColumns = $ctrl.gridApi.getColumnsToToggle(
                                column,
                                allColumns
                            );
                            if (
                                categorySelectedColumns &&
                                categorySelectedColumns.length > 0
                            ) {
                                selectedColumns = selectedColumns.concat(
                                    categorySelectedColumns.map(getColumnName)
                                );
                            }
                        }
                    });
                }
                if (
                    category.subcategories &&
                    category.subcategories.length > 0
                ) {
                    selectedColumns = selectedColumns.concat(
                        getSelectedColumns(category.subcategories)
                    );
                }
            });
            return selectedColumns;
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
            if (
                Object.prototype.hasOwnProperty.call(column.data, 'restApiName')
            ) {
                return column.data.restApiName;
            }
            return column.data.name;
        }

        function rememberCsvConfig() {
            zemLocalStorageService.set(
                KEY_CSV_SEPARATOR,
                $ctrl.config.csvSeparator,
                LOCAL_STORAGE_NAMESPACE
            );
            zemLocalStorageService.set(
                KEY_CSV_DECIMAL_SEPARATOR,
                $ctrl.config.csvDecimalSeparator,
                LOCAL_STORAGE_NAMESPACE
            );
        }
    },
});
