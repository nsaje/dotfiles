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
    };


    function DataSource () {
        var that = this;
        this.data = null;
        this.rows = [];
        this.visibleRows = [];
        this.columns = ['Name'];
        for (var i = 1; i < 11; ++i) {
            this.columns.push('Stat ' + i);
        }

        function parseData (data) {
            var rows = [];
            parseBreakdown(data.breakdown, rows, 1);

            var options = {type: 0, level: 0};
            var gridRow = new GridRow(0, 0, data);
            //rows.push({options: options, data: data.data});
            rows.push(gridRow);

            return rows;
        }

        function parseBreakdown (breakdown, rows, level) {
            angular.forEach(breakdown.rows, function (row) {
                var gridRow = new GridRow(0, level, row);
                rows.push(gridRow);

                if (row.hasOwnProperty('breakdown')) {
                    parseBreakdown(row.breakdown, rows, level + 1);
                }
            });

            // TODO: Move to templates
            // ["...", showMoreTitle + " < show more >", "", "", "", "", "", "", "", "", ""],
            //var showMoreTitle = "[showing " + breakdown.rows.length + " out of " + breakdown.pagination.size + "]";
            var gridRow = new GridRow(1, level, breakdown);
            rows.push(gridRow);

        }

        this.fetchData = function () {
            var config = {
                params: {
                    breakdowns: 'ad_group,age,date',
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

            gridRow.collapse = !gridRow.collapse;

            while (true) {
                if (idx >= this.rows.length) break;

                var child = this.rows[++idx];
                if (child.level <= gridRow.level) break;

                child.visible = !gridRow.collapse;
            }
        };

        this.

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

                var newbreakdown = data.data.breakdown;
                for (var i = 0; i < row.level - 1; ++i) {
                    newbreakdown = newbreakdown.rows[0].breakdown;
                }

                breakdown.rows = breakdown.rows.concat(newbreakdown.rows);
                breakdown.pagination.to = newbreakdown.pagination.to;

                that.rows = parseData(that.data);
                console.log("done parsing");

            }).error(function (data, status, headers, config) {
                console.log('ERROR: ' + status);
            });

        }


        this.fetchData();
    }

    return DataSource;
}]);
