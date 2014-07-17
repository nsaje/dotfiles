/*globals angular,oneApp,options,moment*/
"use strict";

oneApp.factory("zemChartService", function() {
    function load(key, isShown) {
        var cache = localStorage[key];
        var result = true;
        if (cache) {
            cache = JSON.parse(cache);
            if (cache.hasOwnProperty('isShown')) {
                result = cache.isShown;
            }
        }

        return result;
    }

    function save(key, isShown) {
        if (isShown === true || isShown === false) {
            localStorage[key] = JSON.stringify({'isShown': isShown});
        }
    }

    return {
        load: load,
        save: save
    };
});
