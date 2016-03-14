/*globals angular,oneApp,constants,options,moment*/
'use strict';

oneApp.factory('zemDataSourceService', ['$http', '$q', function ($http, $q) {

    function DataSource () {
        var that = this;

        this.breakdowns = ['ad_group', 'age', 'date'];
        this.defaultPagination = [2, 3, 3];
        this.endpoint = '/api/experimental/stats/testdata/';

        this.metaData = null;
        this.data = null;

        this.rows = [];
        this.columns = ['Name'];
        for (var i = 1; i < 11; ++i) {
            this.columns.push('Stat ' + i);
        }
        this.prepareBreakdownConfig = function (breakdown) {
            var level = 0;
            if (breakdown) {
                level = breakdown.level;
            }

            // position = (0,0,1)
            var ranges = [];
            for (var i = 0; i < this.breakdowns.length; ++i) {
                var from = 0;
                var to = this.defaultPagination[i];
                if (breakdown) {
                    if (i + 1 < breakdown.level) {
                        from = breakdown.position[i+1];
                        to = from + 1;
                    } else if (breakdown.level === i + 1) {
                        from = breakdown.pagination.to;
                        to = from + this.defaultPagination[i];
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


        this.fetchInitial = function () {
            var config = this.prepareBreakdownConfig();
            return this.fetch(config);

            //$http.get(this.endpoint, config).success(function (data, status) {
            //    that.data = data.data[0].rows[0];
            //    that.rows = parseData(that.data);
            //}).error(function (data, status, headers, config) {
            //    console.log('ERROR: ' + status);
            //});
        };

        this.fetchMore = function (breakdown) {
            var config = this.prepareBreakdownConfig(breakdown);
            return this.fetch(config);
            //$http.get(this.endpoint, config).success(function (data, status) {
            //    var breakdown = data.data[0];
            //    that.applyBreakdown(breakdown);
            //
            //    var newRows = parseBreakdown(row.parent, breakdown);
            //    var idx = that.rows.indexOf(row);
            //    newRows.pop();
            //    that.rows.splice.apply(that.rows, [idx, 0].concat(newRows)); }).error(function (data, status, headers, config) {
            //    console.log('ERROR: ' + status);
            //});
        };

        // TODO: move to API
        this.fetch = function (config){
            var deferred = $q.defer();
            $http.get(this.endpoint, config).success(function (data, status) {
                var breakdown = data.data[0];
                that.applyBreakdown(breakdown);
                deferred.resolve(breakdown);
            }).error(function (data, status) {
                console.log('ERROR: ' + status);
                deferred.reject(data)
            });

            return deferred.promise;
        }


        //this.fetchInitial();
    }

    return DataSource;
}]);
