angular
    .module('one.widgets')
    .service('zemConversionPixelsEndpoint', function($q, $http, zemUtils) {
        //eslint-disable-line max-len

        this.list = list;
        this.post = post;
        this.put = put;
        this.archive = archive;
        this.restore = restore;

        function list(accountId, audienceEnabledOnly) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + accountId + '/conversion_pixels/';
            if (audienceEnabledOnly) {
                url = url + '?audience_enabled_only=1';
            }

            $http
                .get(url)
                .success(function(data) {
                    deferred.resolve(zemUtils.convertToCamelCase(data.data));
                })
                .error(function() {
                    deferred.reject();
                });

            return deferred.promise;
        }

        function post(accountId, data) {
            var deferred = $q.defer();
            var url = '/api/accounts/' + accountId + '/conversion_pixels/';

            $http
                .post(url, zemUtils.convertToUnderscore(data))
                .success(function(data) {
                    deferred.resolve(zemUtils.convertToCamelCase(data.data));
                })
                .error(function(data, status) {
                    var ret = null;
                    if (
                        status === 400 &&
                        data &&
                        data.data.error_code === 'ValidationError'
                    ) {
                        ret = data.data;
                    }

                    deferred.reject(ret);
                });

            return deferred.promise;
        }

        function put(conversionPixelId, data) {
            var deferred = $q.defer();
            var url = '/api/conversion_pixel/' + conversionPixelId + '/';

            $http
                .put(url, zemUtils.convertToUnderscore(data))
                .success(function(data) {
                    deferred.resolve(zemUtils.convertToCamelCase(data.data));
                })
                .error(function(data, status) {
                    var ret = null;
                    if (
                        status === 400 &&
                        data &&
                        data.data.error_code === 'ValidationError'
                    ) {
                        ret = data.data;
                    }

                    deferred.reject(ret);
                });

            return deferred.promise;
        }

        function archive(conversionPixel) {
            var data = {
                archived: true,
                name: conversionPixel.name,
            };

            return put(conversionPixel.id, data);
        }

        function restore(conversionPixel) {
            var data = {
                archived: false,
                name: conversionPixel.name,
            };

            return put(conversionPixel.id, data);
        }
    });
