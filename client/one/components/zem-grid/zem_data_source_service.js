/* globals oneApp */
'use strict';

oneApp.factory('zemDataSourceService', ['$http', '$q', function ($http, $q) {

    function DataSource () {
        this.breakdowns = ['ad_group', 'age', 'date'];
        this.endpoint = '/api/stats/testdata/';
        this.defaultPagination = [2, 3, 5];

        this.data = null;

        this.prepareBreakdownConfig = function (breakdown, size) {
            var level = 0;
            if (breakdown) level = breakdown.level;

            var ranges = [];
            for (var i = 1; i <= this.breakdowns.length; ++i) {
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

            var config = {
                params: {
                    breakdowns: this.breakdowns.join(','),
                    ranges: ranges.join(','),
                    level: level,
                },
            };

            return config;
        };

        this.applyBreakdown = function (breakdown) {
            if (breakdown.level === 0) {
                this.data = breakdown.rows[0];
                return;
            }

            var position = breakdown.position;
            var current = this.data.breakdown;
            for (var i = 1; i < breakdown.level; ++i) {
                current = current.rows[position[i]].breakdown;
            }

            current.rows = current.rows.concat(breakdown.rows);
            current.pagination.to = breakdown.pagination.to;
            current.pagination.size += breakdown.pagination.size;
        };

        // TODO: move to API
        this.fetch = function (breakdown, size) {
            var config = this.prepareBreakdownConfig(breakdown, size);
            var deferred = $q.defer();
            var that = this;
            $http.get(this.endpoint, config).success(function (data) {
                var breakdown = data.data[0];
                that.applyBreakdown(breakdown);
                deferred.resolve(breakdown);
            }).error(function (data) {
                deferred.reject(data);
            });

            return deferred.promise;
        };
    }

    return DataSource;
}]);
