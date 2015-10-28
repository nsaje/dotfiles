/* globals JSON */
"use strict"

oneApp.factory('zemUserSettings', ['zemLocalStorageService', '$location', function(zemLocalStorageService, $location) {
    function toUnderscore(string){
        return string.replace(/([A-Z])/g, function($1) {
            return '_' + $1.toLowerCase();
        });
    }

    function getFromUrl(key, isArray) {
        var value = $location.search()[toUnderscore(key)];

        if (value && isArray) {
            value = value.split(',');
        }

        if (value === 'true') {
            return true;
        } else if (value === 'false') {
            return false;
        }

        return value;
    }

    function removeFromUrl(key) {
        $location.search(toUnderscore(key), null);
    }

    function getValue(name, namespace, isArray) {
        var value = getFromUrl(name, isArray);

        if (value === undefined) {
            value = zemLocalStorageService.get(name, namespace);
        }

        return value;
    }

    function resetUrlAndGetValue(name, namespace, isArray) {
        removeFromUrl(name);
        return getValue(name, namespace, isArray);
    }

    function addToUrl(key, value, isArray) {
        if (isArray && value && value.length > 0) {
            value = value.join(',');
        }

        $location.search(toUnderscore(key), value);
    }

    function setValue(name, value, namespace, isArray) {
        zemLocalStorageService.set(name, value, namespace);
        addToUrl(name, value, isArray);
    }

    function UserSettings($scope, namespace) {
        var registeredNames = [];

        function register(name, global) {
            var isArray = false;
            if (Object.prototype.toString.call($scope[name]) === '[object Array]') {
                isArray = true;
            }

            var value = getValue(name, global ? null : namespace, isArray);

            if (value !== undefined && $scope[name] !== value) {
                $scope[name] = value;
            }

            $scope.$watch(name, function(newValue, oldValue) {
                if (oldValue !== newValue) {
                    setValue(name, newValue, global ? null : namespace, isArray);
                }
            }, true);

            registeredNames.push(name);
        }

        function registerGlobal(name) {
            register(name, true);
        }

        $scope.$on('$stateChangeStart', function() {
            registeredNames.forEach(function (name) {
                removeFromUrl(name);
            });
        });

        return {
            register: register,
            registerGlobal: registerGlobal
        };
    }

    return {
        getInstance: function($scope, namespace) {
            return new UserSettings($scope, namespace);
        },
        getValue: getValue,
        resetUrlAndGetValue: resetUrlAndGetValue,
        setValue: setValue
    };
}]);
