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
        this.data = null;
        this.rows = [];
        this.columns = ['Name'];
        for (var i = 1; i < 11; ++i) {
            this.columns.push('Stat ' + i);
        }

        this.breakdowns = ['ad_group', 'age', 'date'];
        this.defaultPagination = [3, 4, 5];

        function parseData (data) {
            var gridRow = new GridRow(0, 0, data);
            var rows = parseBreakdown(gridRow, data.breakdown);
            rows.push(gridRow);
            return rows;
        }

        function parseBreakdown (parentGridRow, breakdown) {
            var rows = [];
            var level = breakdown.position.length + 1;

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

        this.fetchData = function () {
            debugger;

            var x = _.range(5);
            var ranges = [[1, this.defaultPagination[0]], [1, this.defaultPagination[1]], []]
            var config = {
                params: {
                    breakdowns: this.breakdowns.join(','),
                    ranges: '1|3,1|3,1|3',
                    //breakdowns: 'ad_group,age',
                    //ranges: '1|10,1|4',
                },
            };


            var url = '/api/experimental/stats/testdata/';
            $http.get(url, config).success(function (data, status) {

                var start = new Date().getTime();
                that.data = data.data;
                that.rows = parseData(that.data);
                var end = new Date().getTime();
                console.log("Parsing took : " + (end - start));

            }).error(function (data, status, headers, config) {
                console.log('ERROR: ' + status);
            });
        };

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

        this.fetchMore = function (row) {
            var breakdown = row.dataRow;

            var qBreakdowns = 'ad_group,age,date';
            var qRanges = '';

            var breakdowns = ['ad_group', 'age', 'date'];
            var ranges = [];

            var from, to;
            for (var i = 0; i < breakdowns.length; ++i) {
                if (row.level > i + 1) {
                    from = breakdown.position[i];
                    to = from + 1;
                } else if (row.level === i + 1) {
                    from = breakdown.pagination.to;
                    to = from + 3;
                } else {
                    from = 1;
                    to = 4;
                }

                ranges.push([from, to].join('|'));
            }

            var config = {
                params: {
                    breakdowns: breakdowns.join(','),
                    ranges: ranges.join(','),
                },
            };

            // check level
            // check parents - ids/num
            console.log("Fetch more");

            var url = '/api/experimental/stats/testdata/';
            $http.get(url, config).success(function (data, status) {

                var start = new Date().getTime();
                var newbreakdown = data.data.breakdown;
                for (var i = 0; i < row.level - 1; ++i) {
                    newbreakdown = newbreakdown.rows[0].breakdown;
                }

                var newRows = parseBreakdown(row.parent, newbreakdown);
                var idx = that.rows.indexOf(row);
                newRows.pop();
                that.rows.splice.apply(that.rows, [idx, 0].concat(newRows));

                breakdown.rows = breakdown.rows.concat(newbreakdown.rows);
                breakdown.pagination.to = newbreakdown.pagination.to;

                console.log("Parsing took : " + (new Date().getTime() - start));

            }).error(function (data, status, headers, config) {
                console.log('ERROR: ' + status);
            });

        }


        this.fetchData();
    }

    return DataSource;
}]);
