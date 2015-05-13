/*globals angular,oneApp,constants,options,moment*/
"use strict";

oneApp.factory("zemDemoCacheService", function() {
    var cache = {},
        ids = {};
    return {
        set: function (key, val) {
            cache[key] = val;
        },
        get: function (key) {
            return cache[key];
        },
        update: function (key, field, val) {
            if (cache[key] === undefined) { cache[key] = {}; }
            cache[key][field] = val;
        },
        generateId: function (type) {
            if (!ids[type]) { ids[type] = 10000; }
            return ids[type]++;
        }
    };
});

