/*globals angular,oneApp,options,moment*/
"use strict";

oneApp.factory("zemCustomTableColsService", function() {
    function load(key, columns) {
        var columnsCache = localStorage[key];
        var cols = [];
        if (columnsCache) {
            cols = JSON.parse(columnsCache);
            columns.forEach(function (x) {
                if (cols.indexOf(x.field) > -1) {
                    x.checked = true;
                } else {
                    x.checked = false;
                }
            });
        }

        return cols;
    }

    function save(key, columns) {
        var cols = [];
        columns.forEach(function (x) {
            if (x.checked) {
                cols.push(x.field);
            }
        });
        localStorage[key] = JSON.stringify(cols);

        return cols;
    }

    return {
        load: load,
        save: save
    };
});
