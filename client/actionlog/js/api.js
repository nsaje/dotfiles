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
    }

    return {
        actionLog: new ActionLog(),
    };
}]);
