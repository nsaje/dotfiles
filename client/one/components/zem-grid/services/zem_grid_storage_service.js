/* globals oneApp */
'use strict';

oneApp.factory('zemGridStorageService', ['zemLocalStorageService', function (zemLocalStorageService) {
    var key = 'columns';

    function loadColumns (grid) {
        var namespace = grid.meta.data.localStoragePrefix;
        var columns = zemLocalStorageService.get(key, namespace);
        if (columns) {
            grid.meta.data.columns.forEach(function (column) {
                column.checked = column.unselectable || columns.indexOf(column.field) > -1;
            });
        } else {
            // Use defaults
        }
    }

    function saveColumns (grid) {
        var namespace = grid.meta.data.localStoragePrefix;
        var columns = [];
        grid.meta.data.columns.forEach(function (x) {
            if (x.checked) {
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
