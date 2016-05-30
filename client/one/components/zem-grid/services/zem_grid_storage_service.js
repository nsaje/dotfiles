/*globals angular,oneApp,options,moment,JSON*/
'use strict';

oneApp.factory('zemGridStorageService', ['zemLocalStorageService', function (zemLocalStorageService) {
    var key = 'columns';

    function loadColumns (grid) {
        var namespace = grid.header.data.localStoragePrefix;
        var cols = zemLocalStorageService.get(key, namespace);
        if (cols) {
            grid.header.data.columns.forEach(function (x) {
                x.checked = x.unselectable || cols.indexOf(x.field) > -1;
            });
        } else {
            // Use defaults - should be already defined
        }
    }

    function saveColumns (grid) {
        var namespace = grid.header.data.localStoragePrefix;
        var columns = grid.header.data.columns.filter(function (x) {
            return x.checked;
        });
        zemLocalStorageService.set(key, columns, namespace);
    }

    return {
        loadColumns: loadColumns,
        saveColumns: saveColumns,
    };
}]);
