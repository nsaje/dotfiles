/* globals angular */
'use strict';

angular.module('one.legacy').factory('zemGridStorageService', ['zemLocalStorageService', function (zemLocalStorageService) {
    var LOCAL_STORAGE_NAMESPACE = 'zem-grid-local-storage';
    var KEY_COLUMNS = 'columns';
    var KEY_COLUMN_PRIMARY_GOAL = 'primary-goal';
    var KEY_ORDER = 'order';
    var DEFAULT_ORDER = '-clicks';

    function loadColumns (grid) {
        var columns = zemLocalStorageService.get(KEY_COLUMNS, LOCAL_STORAGE_NAMESPACE);
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
            if (columns) {
                // Check if it was stored as visible
                var field = column.field;
                var autoSelect = column.data.autoSelect;
                if (column.data.goal && column.data.default) field = KEY_COLUMN_PRIMARY_GOAL;
                column.visible = columns.indexOf(field) > -1;
                if (autoSelect) {
                    column.visible = columns.indexOf(autoSelect) > -1;
                }
            } else {
                // When no storage available use default value
                column.visible = column.data.default;
            }
        });
    }

    function saveColumns (grid) {
        // Save column states - persist state for columns that are not available in current grid
        var columns = zemLocalStorageService.get(KEY_COLUMNS, LOCAL_STORAGE_NAMESPACE) || [];
        grid.header.columns.forEach(function (column) {
            var field = column.field;
            if (column.data.goal && column.data.default) field = KEY_COLUMN_PRIMARY_GOAL;

            var idx = columns.indexOf(field);
            if (column.visible && idx < 0) {
                columns.push(field);
            }
            if (!column.visible && idx >= 0) {
                columns.splice(idx, 1);
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

    function intersects (array1, array2) {
        // TODO: move to util service
        // Simple solution for finding if arrays are having common element
        return array1.filter(function (n) {
            return array2.indexOf(n) != -1;
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
}]);
