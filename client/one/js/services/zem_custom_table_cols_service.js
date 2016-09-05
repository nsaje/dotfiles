/*globals angular,options,moment,JSON*/
'use strict';

angular.module('one.legacy').factory('zemCustomTableColsService', ['zemLocalStorageService', function (zemLocalStorageService) {
    var key = 'columns';

    function load (namespace, columns) {
        var cols = zemLocalStorageService.get(key, namespace);
        if (cols) {
            columns.forEach(function (x) {
                x.checked = x.unselectable || cols.indexOf(x.field) > -1;
            });
        }
    }

    function save (namespace, columns) {
        var cols = [];
        columns.forEach(function (x) {
            if (x.checked) {
                cols.push(x.field);
            }
        });
        zemLocalStorageService.set(key, cols, namespace);
        return cols;
    }

    return {
        load: load,
        save: save
    };
}]);
