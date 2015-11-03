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

        function isArray(value) {
            return Object.prototype.toString.call(value) === '[object Array]';
        }

        function register(name, global) {
            registerWithoutWatch(name, global);

            $scope.$watch(name, function(newValue, oldValue) {
                if (oldValue !== newValue) {
                    setValue(name, newValue, global ? null : namespace, isArray($scope[name]));
                }
            }, true);
        }

        function registerWithoutWatch(name, global) {
            console.log(name);
            console.log(global);
            var value = getValue(name, global ? null : namespace, isArray($scope[name]));

            if (value !== undefined && $scope[name] !== value) {
                $scope[name] = value;
            }

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
            registerGlobal: registerGlobal,
            registerWithoutWatch: registerWithoutWatch
        };
    }

    return {
        getInstance: function($scope, namespace) {
            return new UserSettings($scope, namespace);
        },
        getValue: getValue,
        setValue: setValue
    };
}]);
