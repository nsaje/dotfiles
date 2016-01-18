/* globals JSON */
'use strict';

oneApp.factory('zemLocalStorageService', function () {
    var user = null;

    function getKey (key, namespace) {
        var components = ['oneApp', user.id];

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

    function init (currentUser) {
        user = currentUser;
    }

    return {
        init: init,
        get: get,
        set: set
    };
});
