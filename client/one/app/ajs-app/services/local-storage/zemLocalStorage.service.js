angular
    .module('one.services')
    .factory('zemLocalStorageService', function(zemAuthStore) {
        function getKey(key, namespace) {
            // FIXME: Some tests fails, because current().id throws error, since there is not current user configured
            var user = zemAuthStore.getCurrentUser();
            var id = user ? user.id : undefined;
            var components = ['oneApp', id];

            if (namespace) {
                components.push(namespace);
            }
            components.push(key);

            return components.join('.');
        }

        function set(key, value, namespace) {
            localStorage.setItem(getKey(key, namespace), JSON.stringify(value));
        }

        function get(key, namespace) {
            var value = localStorage.getItem(getKey(key, namespace));

            if (!value || value === 'undefined') {
                return;
            }

            return JSON.parse(value);
        }

        return {
            get: get,
            set: set,
        };
    });
