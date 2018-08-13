angular
    .module('one.widgets')
    .service('zemCustomAudiencesEndpoint', function($q, $http, zemUtils) {
        //eslint-disable-line max-len

        this.get = get;
        this.list = list;
        this.post = post;
        this.put = put;
        this.archive = archive;
        this.restore = restore;

        function get(accountId, audienceId) {
            var deferred = $q.defer();
            var url =
                '/api/accounts/' + accountId + '/audiences/' + audienceId + '/';

            $http
                .get(url)
                .success(function(data) {
                    var resource = zemUtils.convertToCamelCase(data.data);
                    deferred.resolve(resource);
                })
                .error(function(data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        }

        function list(accountId, includeArchived, includeSize) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + accountId + '/audiences/';

            var config = {params: {}};
            if (includeArchived) config.params.include_archived = '1';
            if (includeSize) config.params.include_size = '1';

            $http
                .get(url, config)
                .success(function(data) {
                    var resource = [];

                    if (data && data.data) {
                        resource = data.data.map(function(d) {
                            var converted = zemUtils.convertToCamelCase(d);
                            converted.createdDt = moment(
                                converted.createdDt
                            ).toDate();
                            return converted;
                        });
                    }

                    deferred.resolve(resource);
                })
                .error(function(data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        }

        function post(accountId, audience) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + accountId + '/audiences/';

            $http
                .post(url, audience)
                .success(function(data) {
                    var resource = zemUtils.convertToCamelCase(data.data);
                    deferred.resolve(resource);
                })
                .error(function(data, status) {
                    var ret = null;
                    if (
                        status === 400 &&
                        data &&
                        data.data.error_code === 'ValidationError'
                    ) {
                        ret = zemUtils.convertToCamelCase(data.data.errors);
                    }
                    deferred.reject(ret);
                });

            return deferred.promise;
        }

        function put(accountId, audienceId, audience) {
            var deferred = $q.defer();
            var url =
                '/api/accounts/' + accountId + '/audiences/' + audienceId + '/';

            $http
                .put(url, audience)
                .success(function(data) {
                    var resource = zemUtils.convertToCamelCase(data.data);
                    deferred.resolve(resource);
                })
                .error(function(data, status) {
                    var ret = null;
                    if (
                        status === 400 &&
                        data &&
                        data.data.error_code === 'ValidationError'
                    ) {
                        ret = zemUtils.convertToCamelCase(data.data.errors);
                    }
                    deferred.reject(ret);
                });

            return deferred.promise;
        }

        function archive(accountId, audienceId) {
            var deferred = $q.defer();
            var url =
                '/api/accounts/' +
                accountId +
                '/audiences/' +
                audienceId +
                '/archive/';
            var config = {
                params: {},
            };

            var data = {};

            $http
                .post(url, data, config)
                .success(function() {
                    deferred.resolve();
                })
                .error(function(data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        }

        function restore(accountId, audienceId) {
            var deferred = $q.defer();
            var url =
                '/api/accounts/' +
                accountId +
                '/audiences/' +
                audienceId +
                '/restore/';

            var config = {
                params: {},
            };

            var data = {};

            $http
                .post(url, data, config)
                .success(function() {
                    deferred.resolve();
                })
                .error(function(data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        }
    });
