/*globals angular,oneApp,options,moment,JSON*/
'use strict';

oneApp.factory('zemGridStorageService', ['zemLocalStorageService', function (zemLocalStorageService) {
    var key = 'columns';

    function loadColumns (grid) {
        var namespace = grid.meta.data.localStoragePrefix;
        var cols = zemLocalStorageService.get(key, namespace);
        if (cols) {
            grid.meta.data.columns.forEach(function (x) {
                x.checked = x.unselectable || cols.indexOf(x.field) > -1;
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
