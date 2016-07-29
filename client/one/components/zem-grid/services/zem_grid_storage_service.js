/* globals oneApp */
'use strict';

oneApp.factory('zemGridStorageService', ['zemLocalStorageService', function (zemLocalStorageService) {
    var LOCAL_STORAGE_NAMESPACE = 'zem-grid-local-storage';
    var KEY_COLUMNS = 'columns';
    var KEY_COLUMN_PRIMARY_GOAL = 'primary-goal';

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
                if (column.data.goal && column.data.default) field = KEY_COLUMN_PRIMARY_GOAL;
                column.visible = columns.indexOf(field) > -1;
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

            var idx = columns.indexOf (field);
            if (column.visible && idx < 0) {
                columns.push(field);
            }
            if (!column.visible && idx >= 0) {
                columns.splice(idx, 1);
            }
        });
        zemLocalStorageService.set(KEY_COLUMNS, columns, LOCAL_STORAGE_NAMESPACE);
    }

    return {
        loadColumns: loadColumns,
        saveColumns: saveColumns,
    };
}]);
