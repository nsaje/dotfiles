angular
    .module('one.services')
    .service('zemUserEndpoint', function($q, $http, zemUtils) {
        //
        // Public API
        //
        this.create = create;
        this.remove = remove;
        this.list = list;
        this.get = get;

        function create(accountId, user) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + accountId + '/users/';

            var data = zemUtils.convertToUnderscore(user);

            $http
                .put(url, data)
                .success(function(data, status) {
                    deferred.resolve({
                        user: data.data.user,
                        created: status === 201,
                    });
                })
                .error(function(data, status) {
                    var resource = {};
                    if (
                        status === 400 &&
                        data &&
                        data.data.error_code === 'ValidationError'
                    ) {
                        resource.errors = zemUtils.convertToCamelCase(
                            data.data.errors
                        );
                        resource.message = data.data.message;
                    }

                    deferred.reject(resource);
                });

            return deferred.promise;
        }

        function remove(accountId, userId, fromAllAccounts) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + accountId + '/users/' + userId + '/';
            if (fromAllAccounts) {
                url += '?remove_from_all_accounts=1';
            }

            $http
                .delete(url)
                .success(function(data) {
                    deferred.resolve(data.data);
                })
                .error(function(data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        }

        function list(accountId) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + accountId + '/users/';

            $http
                .get(url)
                .success(function(data) {
                    deferred.resolve(data.data);
                })
                .error(function(data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        }

        function get(id) {
            var deferred = $q.defer();
            var url = '/api/users/' + id + '/';
            var config = {
                params: {},
            };

            $http
                .get(url, config)
                .success(function(data) {
                    var user;
                    if (data && data.data) {
                        var apiUser = data.data.user;
                        user = zemUtils.convertToCamelCase(apiUser);
                        // Revert permission back to original format (underscore)
                        user.permissions = apiUser.permissions;
                    }
                    deferred.resolve(user);
                })
                .error(function(data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        }
    });
