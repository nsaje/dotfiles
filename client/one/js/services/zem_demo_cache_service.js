/*globals angular,constants,options,moment*/
'use strict';

angular.module('one.legacy').factory('zemDemoCacheService', function () {
    var FIRST_ID = 1000000,
        cache = {},
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
            if (!ids[type]) { ids[type] = FIRST_ID; }
            return ids[type]++;
        }
    };
});

