angular.module('one.widgets').factory('zemGridStorageService', function (zemLocalStorageService, zemNavigationNewService) { // eslint-disable-line max-len
    var LOCAL_STORAGE_NAMESPACE = 'zemGrid';
    var ALL_ACCOUNTS_KEY = 'allAccounts';
    var KEY_COLUMNS = 'columns';
    var KEY_COLUMN_PRIMARY_GOAL = 'primaryGoal';
    var KEY_ORDER = 'order';
    var DEFAULT_ORDER = '-clicks';

    function loadColumns (grid) {
        var accountKey = getAccountKey(grid.meta.data.level, zemNavigationNewService.getActiveAccount());
        var columns = zemLocalStorageService.get(KEY_COLUMNS, LOCAL_STORAGE_NAMESPACE) || {};

        grid.header.columns.forEach(function (column) {
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
            if (columns[accountKey]) {
                // Check if it was stored as visible
                var field = column.field;
                var autoSelect = column.data.autoSelect;
                if (column.data.goal && column.data.default) field = KEY_COLUMN_PRIMARY_GOAL;
                column.visible = columns[accountKey].indexOf(field) > -1;
                if (autoSelect) {
                    column.visible = columns[accountKey].indexOf(autoSelect) > -1;
                }
            } else {
                // When no storage available use default value
                column.visible = column.data.default;
            }
        });
    }

    function saveColumns (grid) {
        var accountKey = getAccountKey(grid.meta.data.level, zemNavigationNewService.getActiveAccount());
        var columns = zemLocalStorageService.get(KEY_COLUMNS, LOCAL_STORAGE_NAMESPACE) || {};
        if (!columns[accountKey]) {
            columns[accountKey] = [];
        }

        grid.header.columns.forEach(function (column) {
            var field = column.field;
            if (column.data.goal && column.data.default) field = KEY_COLUMN_PRIMARY_GOAL;

            var idx = columns[accountKey].indexOf(field);
            if (column.visible && idx < 0) {
                columns[accountKey].push(field);
            }
            if (!column.visible && idx >= 0) {
                columns[accountKey].splice(idx, 1);
            }
        });

        zemLocalStorageService.set(KEY_COLUMNS, columns, LOCAL_STORAGE_NAMESPACE);
    }

    function loadOrder (grid) {
        // Load order from local storage
        // If order is used for column that is not available in
        // current configuration (level, breakdown) use default one (-clicks)
        var order = zemLocalStorageService.get(KEY_ORDER, LOCAL_STORAGE_NAMESPACE) || DEFAULT_ORDER;

        var orderField = order;
        if (orderField[0] === '-') orderField = orderField.substr(1);
        var column = grid.meta.data.columns.filter(function (column) {
            return orderField === (column.orderField || column.field);
        })[0];

        if (!column) order = DEFAULT_ORDER;

        if (column && column.breakdowns) {
            // check if column is available in current breakdown configuration
            var breakdowns = grid.meta.dataService.getBreakdown().map(function (breakdown) {
                return breakdown.query;
            });
            if (!intersects(column.breakdowns, breakdowns)) {
                order = DEFAULT_ORDER;
            }
        }

        grid.meta.dataService.setOrder(order, false);
    }

    function getAccountKey (level, activeAccount) {
        if (level === constants.level.ALL_ACCOUNTS) {
            return ALL_ACCOUNTS_KEY;
        } else if (activeAccount) {
            return activeAccount.id.toString();
        }
    }

    function intersects (array1, array2) {
        // TODO: move to util service
        // Simple solution for finding if arrays are having common element
        return array1.filter(function (n) {
            return array2.indexOf(n) !== -1;
        }).length > 0;
    }

    function saveOrder (grid) {
        var order = grid.meta.dataService.getOrder();
        zemLocalStorageService.set(KEY_ORDER, order, LOCAL_STORAGE_NAMESPACE);
    }

    return {
        loadColumns: loadColumns,
        saveColumns: saveColumns,
        saveOrder: saveOrder,
        loadOrder: loadOrder,
    };
});
