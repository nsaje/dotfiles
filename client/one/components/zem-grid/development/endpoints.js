/* globals oneApp,angular */
'use strict';

oneApp.factory('zemDataSourceDebugEndpoints', ['$rootScope', '$controller', '$http', '$q', '$timeout', 'api', function ($rootScope, $controller, $http, $q, $timeout, api) { // eslint-disable-line max-len

    function MockEndpoint () {
        var url = '/api/stats/testdata/';
        this.availableBreakdowns = ['ad_group', 'age', 'sex', 'date'];
        this.defaultBreakdown = ['ad_group', 'age', 'date'];
        this.defaultPagination = [2, 3, 5, 7];

        this.getMetaData = function (config) {
            var deferred = $q.defer();
            $http.get(url, this.createQueryParams(config)).success(function (data) {
                var breakdown = data.data[0];
                deferred.resolve(breakdown.meta);
            }).error(function (data) {
                deferred.reject(data);
            });

            return deferred.promise;
        };

        this.getData = function (config) {
            var deferred = $q.defer();
            $http.get(url, this.createQueryParams(config)).success(function (data) {
                deferred.resolve(data.data[0]);
            }).error(function (data) {
                deferred.reject(data);
            });

            return deferred.promise;
        };

        this.createQueryParams = function (config) {
            var breakdown = config.breakdown;
            var size = config.size;
            var level = 0;
            if (breakdown) level = breakdown.level;

            var ranges = [];
            for (var i = 1; i <= config.selectedBreakdown.length; ++i) {
                var from = 0;
                var to = this.defaultPagination[i - 1];
                if (breakdown) {
                    if (i < breakdown.level) {
                        from = breakdown.position[i];
                        to = from + 1;
                    } else if (breakdown.level === i) {
                        from = breakdown.pagination.to;
                        if (size) {
                            if (size > 0) to = from + size;
                            else to = -1;
                        } else {
                            to = from + this.defaultPagination[i - 1];
                        }
                    }
                }
                ranges.push([from, to].join('|'));
            }

            return {
                params: {
                    breakdowns: config.selectedBreakdown.join(','),
                    ranges: ranges.join(','),
                    level: level,
                },
            };
        };
    }
    return {
        createMockEndpoint: function () {
            return new MockEndpoint();
        },
    };
}]);
