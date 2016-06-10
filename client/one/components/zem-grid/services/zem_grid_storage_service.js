/* globals oneApp */
'use strict';

oneApp.factory('zemGridStorageService', ['zemLocalStorageService', function (zemLocalStorageService) {
    var key = 'columns';

    function loadColumns (grid) {
        var namespace = grid.meta.data.localStoragePrefix;
        var columns = zemLocalStorageService.get(key, namespace);
        grid.header.columns.forEach(function (column) {
            if (!column.data.shown) {
                // If column shouldn't be shown (e.g. permissions) set visibility to false
                column.visible = false;
                return;
            }
            if (column.data.unselectable) {
                // Always visible columns
                column.visible = true;
                return;
            }
            if (columns) {
                // Check if it was stored as visible
                column.visible = columns.indexOf(column.field) > -1;
            } else {
                // When no storage available use default value
                column.visible = column.data.checked;
            }
        });
    }

    function saveColumns (grid) {
        var namespace = grid.meta.data.localStoragePrefix;
        var columns = [];
        grid.header.columns.forEach(function (column) {
            if (column.visible) {
                columns.push(column.field);
            }
        });
        zemLocalStorageService.set(key, columns, namespace);
    }

    return {
        loadColumns: loadColumns,
        saveColumns: saveColumns,
    };
}]);
