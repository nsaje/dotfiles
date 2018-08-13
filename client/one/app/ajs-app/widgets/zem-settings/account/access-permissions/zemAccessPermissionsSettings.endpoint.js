angular
    .module('one.widgets')
    .service('zemAccessPermissionsSettingsEndpoint', function($q, $http) {
        this.post = post;

        function post(accountId, userId, action) {
            var deferred = $q.defer();
            var url =
                '/api/accounts/' +
                accountId +
                '/users/' +
                userId +
                '/' +
                action;
            var config = {params: {}};

            $http
                .post(url, config)
                .then(function(data) {
                    deferred.resolve(data.data);
                })
                .catch(function(error) {
                    deferred.reject(error);
                });
            return deferred.promise;
        }
    });
