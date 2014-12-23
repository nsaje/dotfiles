/* globals JSON */
"use strict"

oneApp.factory('zemUserSettings', ['zemLocalStorageService', '$location', function(zemLocalStorageService, $location) {
    function UserSettings($scope, namespace) {
        var registeredNames = [];

        function toUnderscore(string){
            return string.replace(/([A-Z])/g, function($1) {
                return '_' + $1.toLowerCase();
            });
        }

        function addToUrl(key, value) {
            $location.search(toUnderscore(key), value);
        }

        function getFromUrl(key) {
            var value = $location.search()[toUnderscore(key)];

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

        function register(name, global) {
            var value = getFromUrl(name);

            if (value === undefined) {
                value = zemLocalStorageService.get(name, global ? null : namespace);
            }

            if (value !== undefined && $scope[name] !== value) {
                $scope[name] = value;
            }

            $scope.$watch(name, function(newValue, oldValue) {
                if (oldValue !== newValue) {
                    zemLocalStorageService.set(name, newValue, global ? null : namespace);
                    addToUrl(name, newValue);
                }
            });

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
        }
    };
}]);
