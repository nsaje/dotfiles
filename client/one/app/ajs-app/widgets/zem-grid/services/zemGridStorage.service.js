angular
    .module('one.widgets')
    .factory('zemGridStorageService', function(
        zemLocalStorageService,
        zemNavigationNewService,
        zemCostModeService,
        zemUtils
    ) {
        // eslint-disable-line max-len
        var LOCAL_STORAGE_NAMESPACE = 'zemGrid';
        var ALL_ACCOUNTS_KEY = 'allAccounts';
        var KEY_COLUMNS = 'columns';
        var KEY_COLUMN_PRIMARY_GOAL = 'primaryGoal';
        var KEY_ORDER = 'order';
        var DEFAULT_ORDER = '-clicks';

        function loadColumns(grid) {
            // load columns that can be shown in the grid
            var accountKey = getAccountKey(
                grid.meta.data.level,
                zemNavigationNewService.getActiveAccount()
            );
            var storedColumns =
                zemLocalStorageService.get(
                    KEY_COLUMNS,
                    LOCAL_STORAGE_NAMESPACE
                ) || {};

            grid.header.columns.forEach(function(column) {
                // 1. get all available columns that user has access to
                if (!column.data.shown) {
                    // If column shouldn't be shown (e.g. permissions) set visibility to false
                    column.visible = false;
                    return;
                }
                if (column.data.permanent) {
                    // Always visible columns
                    column.visible = true;
                    return;
                }

                // 2. make them visible based on user selection
                if (storedColumns[accountKey]) {
                    // Check if it was stored as visible
                    var field = column.field;
                    var autoSelect = column.data.autoSelect;

                    if (column.data.goal && column.data.default)
                        field = KEY_COLUMN_PRIMARY_GOAL;
                    column.visible =
                        storedColumns[accountKey].indexOf(field) > -1;

                    if (autoSelect) {
                        // select a coresponding column
                        column.visible =
                            storedColumns[accountKey].indexOf(autoSelect) > -1;
                    }
                } else {
                    // When no storage available use default value
                    column.visible = column.data.default;
                }
            });

            selectRelevantCostMode(grid);
        }

        function selectRelevantCostMode(grid) {
            var groupedAvailabeColumns = {};
            var globalCostMode = zemCostModeService.getCostMode();
            var oppositeCostMode = zemCostModeService.getOppositeCostMode(
                globalCostMode
            );

            if (!zemCostModeService.isTogglableCostMode(globalCostMode)) return;

            // group columns by fieldGroup and costMode
            grid.header.columns.forEach(function(column) {
                if (!column.data.shown) return;

                if (column.data.fieldGroup) {
                    if (
                        !groupedAvailabeColumns.hasOwnProperty(
                            column.data.fieldGroup
                        )
                    ) {
                        groupedAvailabeColumns[column.data.fieldGroup] = {};
                    }
                    groupedAvailabeColumns[column.data.fieldGroup][
                        column.data.costMode
                    ] = column;
                }
            });

            // make columns from current cost mode visible and their costMode pairs invisible
            Object.keys(groupedAvailabeColumns).forEach(function(fieldGroup) {
                var columnGroup = groupedAvailabeColumns[fieldGroup];
                var anyVisible = zemCostModeService.TOGGLABLE_COST_MODES.some(
                    function(costMode) {
                        return (
                            columnGroup[costMode] &&
                            columnGroup[costMode].visible
                        );
                    }
                );

                if (anyVisible) {
                    if (columnGroup[globalCostMode])
                        columnGroup[globalCostMode].visible = true;
                    if (columnGroup[oppositeCostMode])
                        columnGroup[oppositeCostMode].visible = false;
                }
            });
        }

        function saveColumns(grid) {
            var accountKey = getAccountKey(
                grid.meta.data.level,
                zemNavigationNewService.getActiveAccount()
            );
            var columns =
                zemLocalStorageService.get(
                    KEY_COLUMNS,
                    LOCAL_STORAGE_NAMESPACE
                ) || {};
            if (!columns[accountKey]) {
                columns[accountKey] = [];
            }

            grid.header.columns.forEach(function(column) {
                var field = column.field;
                if (column.data.goal && column.data.default)
                    field = KEY_COLUMN_PRIMARY_GOAL;

                var idx = columns[accountKey].indexOf(field);
                if (column.visible && idx < 0) {
                    columns[accountKey].push(field);
                }
                if (!column.visible && idx >= 0) {
                    columns[accountKey].splice(idx, 1);
                }
            });

            zemLocalStorageService.set(
                KEY_COLUMNS,
                columns,
                LOCAL_STORAGE_NAMESPACE
            );
        }

        function loadOrder(grid) {
            // Load order from local storage
            // If order is used for column that is not available in
            // current configuration (level, breakdown) use default one (-clicks)
            var order =
                zemLocalStorageService.get(
                    KEY_ORDER,
                    LOCAL_STORAGE_NAMESPACE
                ) || DEFAULT_ORDER;

            var orderField = order;
            if (orderField[0] === '-') orderField = orderField.substr(1);
            var column = grid.meta.data.columns.filter(function(column) {
                return orderField === (column.orderField || column.field);
            })[0];

            if (!column) order = DEFAULT_ORDER;

            if (column && column.breakdowns) {
                // check if column is available in current breakdown configuration
                var breakdowns = grid.meta.dataService
                    .getBreakdown()
                    .map(function(breakdown) {
                        return breakdown.query;
                    });
                if (!zemUtils.intersects(column.breakdowns, breakdowns)) {
                    order = DEFAULT_ORDER;
                }
            }

            grid.meta.api.setOrder(order);
        }

        function getAccountKey(level, activeAccount) {
            if (level === constants.level.ALL_ACCOUNTS) {
                return ALL_ACCOUNTS_KEY;
            } else if (activeAccount) {
                return activeAccount.id.toString();
            }
        }

        function saveOrder(grid) {
            var order = grid.meta.api.getOrder();
            zemLocalStorageService.set(
                KEY_ORDER,
                order,
                LOCAL_STORAGE_NAMESPACE
            );
        }

        return {
            loadColumns: loadColumns,
            saveColumns: saveColumns,
            saveOrder: saveOrder,
            loadOrder: loadOrder,
        };
    });
