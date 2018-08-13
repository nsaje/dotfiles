angular
    .module('one.widgets')
    .service('zemAccessPermissionsEndpoint', function($q, $http) {
        this.post = post;

        function post(accountId, userId, action) {
            var url =
                '/api/accounts/' +
                accountId +
                '/users/' +
                userId +
                '/' +
                action;
            var config = {params: {}};

            var deferred = $q.defer();
            $http
                .post(url, config)
                .success(function(data) {
                    deferred.resolve(data.data);
                })
                .error(function(data) {
                    deferred.reject(data);
                });
            return deferred.promise;
        }
    });
