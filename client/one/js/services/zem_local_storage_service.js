/* globals JSON, angular */
'use strict';

angular.module('one.legacy').factory('zemLocalStorageService', ['zemUserService', function (zemUserService) {
    function getKey (key, namespace) {
        var components = ['oneApp', zemUserService.getUserId()];

        if (namespace) {
            components.push(namespace);
        }
        components.push(key);

        return components.join('.');
    }

    function set (key, value, namespace) {
        localStorage.setItem(
            getKey(key, namespace),
            JSON.stringify(value)
        );
    }

    function get (key, namespace) {
        var value = localStorage.getItem(
            getKey(key, namespace)
        );

        if (!value || value === 'undefined') {
            return;
        }

        return JSON.parse(value);
    }

    return {
        get: get,
        set: set
    };
}]);
