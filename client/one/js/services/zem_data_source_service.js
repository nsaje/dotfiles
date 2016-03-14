/*globals angular,oneApp,constants,options,moment*/
'use strict';

oneApp.factory('zemDataSourceService', ['$http', function ($http) {

    function GridRow (type, level, dataRow) {
        this.dataRow = dataRow;
        this.data = dataRow.data;

        this.level = level;
        this.type = type;

        this.collapsed = false;
        this.visible = true;

        this.parent = null;
    }


    function DataSource () {
        var that = this;

        this.breakdowns = ['ad_group', 'age', 'date'];
        this.defaultPagination = [3, 4, 5];
        this.endpoint = '/api/experimental/stats/testdata/';

        this.metaData = null;
        this.data = null;

        this.rows = [];
        this.columns = ['Name'];
        for (var i = 1; i < 11; ++i) {
            this.columns.push('Stat ' + i);
        }


        function parseData (data) {
            var gridRow = new GridRow(0, 0, data);
            var rows = parseBreakdown(gridRow, data.breakdown);
            rows.push(gridRow);
            return rows;
        }

        function parseBreakdown (parentGridRow, breakdown) {
            var rows = [];
            var level = breakdown.level;

            angular.forEach(breakdown.rows, function (row) {
                var gridRow = new GridRow(0, level, row);
                gridRow.parent = parentGridRow;
                rows.push(gridRow);
                if (row.hasOwnProperty('breakdown')) {
                    rows = rows.concat(parseBreakdown(gridRow, row.breakdown));
                }
            });

            var gridRow = new GridRow(1, level, breakdown);
            gridRow.parent = parentGridRow;
            rows.push(gridRow);

            return rows;
        }

        this.toggleCollapse = function (gridRow) {

            var idx = this.rows.indexOf(gridRow);

            gridRow.collapsed = !gridRow.collapsed;

            while (true) {
                if (idx >= this.rows.length) break;

                var child = this.rows[++idx];
                if (child.level <= gridRow.level) break;

                child.visible = !gridRow.collapsed && !child.parent.collapsed;
            }
        };

        this.prepareBreakdownConfig = function (breakdown) {
            var level = 0;
            if (breakdown) {
                level = breakdown.level;
            }

            var ranges = [];
            for (var i = 0; i < this.breakdowns.length; ++i) {
                var from = 0;
                var to = this.defaultPagination[i];
                if (breakdown) {
                    if (i + 1 < breakdown.level) {
                        from = breakdown.position[i];
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

        this.insertBreakdown = function (breakdown) {

            if (breakdown.level === 0) {
                this.data = breakdown.rows[0];
                return;
            }

            var position = breakdown.position
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
            $http.get(this.endpoint, config).success(function (data, status) {
                that.data = data.data[0].rows[0];
                that.rows = parseData(that.data);
            }).error(function (data, status, headers, config) {
                console.log('ERROR: ' + status);
            });
        };

        this.fetchMore = function (row) {
            var breakdown = row.dataRow;

            var config = this.prepareBreakdownConfig(breakdown);

            $http.get(this.endpoint, config).success(function (data, status) {
                var breakdown = data.data[0];
                that.insertBreakdown(breakdown);

                var newRows = parseBreakdown(row.parent, breakdown);
                var idx = that.rows.indexOf(row);
                newRows.pop();
                that.rows.splice.apply(that.rows, [idx, 0].concat(newRows)); }).error(function (data, status, headers, config) {
                console.log('ERROR: ' + status);
            });

        };


        this.fetchInitial();
    }

    return DataSource;
}]);
