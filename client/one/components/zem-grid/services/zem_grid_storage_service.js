/* globals oneApp */
'use strict';

oneApp.factory('zemGridStorageService', ['zemLocalStorageService', function (zemLocalStorageService) {
    var key = 'columns';

    function loadColumns (grid) {
        var namespace = grid.meta.data.localStoragePrefix;
        var columns = zemLocalStorageService.get(key, namespace);
        grid.meta.data.columns.forEach(function (column) {
            if (columns) {
                column.visible = column.shown && (columns.indexOf(column.field) > -1 || column.unselectable);
            } else {
                column.visible = column.shown && (column.checked || column.unselectable);
            }
        });
    }

    function saveColumns (grid) {
        var namespace = grid.meta.data.localStoragePrefix;
        var columns = [];
        grid.meta.data.columns.forEach(function (x) {
            if (x.visible) {
                columns.push(x.field);
            }
        });
        zemLocalStorageService.set(key, columns, namespace);
    }

    return {
        loadColumns: loadColumns,
        saveColumns: saveColumns,
    };
}]);
