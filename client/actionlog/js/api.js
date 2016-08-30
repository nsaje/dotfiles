/*globals angular,oneApp,constants,options,moment*/
'use strict';

actionLogApp.factory('api', ['$http', '$q', function ($http, $q) {
    function ActionLog () {
        this.list = function (filters) {
            var deferred = $q.defer();
            var url = '/action_log/api/';
            var config = {
                params: {
                    filters: filters
                }
            };

            $http.get(url, config).
                success(function (data, status) {
                    var resource;
                    if (data && data.data) {
                        resource = data.data;
                    }
                    deferred.resolve(resource);
                }).
                error(function (data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        this.save_state = function (action_id, new_state) {
            var deferred = $q.defer();
            var url = '/action_log/api/' + action_id + '/';
            var config = {
                params: {}
            };

            var data = {
                state: new_state
            };

            $http.put(url, data, config).
                success(function (data, status) {
                    var resource;
                    if (data && data.data) {
                        resource = data.data;
                    }
                    deferred.resolve(resource);
                }).
                error(function (data, status, headers, config) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        this.updateOutbrainSourcePixel = function(pixelId, pixelUrl, sourcePixelId) {
            var deferred = $q.defer();
            var url = '/action_log/pixel_api/';

            var data = {
                'pixel_id': pixelId,
                'source_type': 'outbrain',
                'url': pixelUrl,
                'source_pixel_id': sourcePixelId,
            };

            $http.put(url, data).success(function (data, status) {
                var resource;
                if (data && data.data) {
                    resource = data.data;
                }
                deferred.resolve(resource);
            }).error(function (data, status, headers, config) {
                if (status === 400 && data && data.data.error_code === 'ValidationError') {
                    data = convertErrorsFromApi(data.data.errors);
                }
                deferred.reject(data);
            });
            return deferred.promise;
        };

        function convertErrorsFromApi (errors) {
            return {
                url: errors.url,
                pixelId: errors.source_pixel_id,
            };
        }
    }

    return {
        actionLog: new ActionLog(),
    };
}]);
