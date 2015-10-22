/*globals angular,oneApp,options,moment,JSON*/
"use strict";

oneApp.factory("zemCustomTableColsService", ['zemLocalStorageService', function(zemLocalStorageService) {
    var key = 'columns';

    function load(namespace, columns) {
        var cols = zemLocalStorageService.get(key, namespace);
        if (cols && cols.length) {
            columns.forEach(function (x) {
                x.checked = x.unselectable || cols.indexOf(x.field) > -1;
            });
        } else {
            // the initial value hasn't been saved yet
            setDefaults(namespace, columns);
        }
    }

    function setDefaults(namespace, columns) {
        var cols = [];
        columns.forEach(function (x) {
            if (x.checked) {
                cols.push(x.field);
            }
        });
        zemLocalStorageService.set(key, cols, namespace);
        return cols;
    }

    function setColumn(namespace, column) {
        var cols = zemLocalStorageService.get(key, namespace) || [];
        var ix = cols.indexOf(column.field);

        if (column.checked && ix === -1) {
            cols.push(column.field);
        } else if (!column.checked && ix > -1) {
            cols.splice(ix, 1);
        }

        zemLocalStorageService.set(key, cols, namespace);
    }

    return {
        load: load,
        setColumn: setColumn
    };
}]);
