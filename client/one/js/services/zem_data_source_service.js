/*globals angular,oneApp,constants,options,moment*/
'use strict';

oneApp.factory('zemDataSourceService', ['$http', function ($http) {


    function DataSource () {
        var that = this;
        this.rows = [];
        this.columns = ['Name'];
        for (var i = 1; i < 11; ++i) {
            this.columns.push('Stat ' + i);
        }

        function parseData (data) {
            var rows = [];
            parseBreakdown(data.breakdown, rows, 1);

            var options = {type: 0, level: 0};
            rows.push({options: options, data: data.data});

            return rows;
        }

        function parseBreakdown (breakdown, rows, level) {
            angular.forEach(breakdown.rows, function (row) {
                var options = {type: 0, level: level};
                rows.push({options: options, data: row.data});

                if (row.hasOwnProperty('breakdown')) {
                    parseBreakdown(row.breakdown, rows, level + 1);
                }
            });

            // TODO: Move to templates
            var options = {type: 0, level: level};
            var showMoreTitle = "[showing " + breakdown.rows.length + " out of " + breakdown.pagination.size + "]";
            rows.push({
                options: options,
                data: ["...", showMoreTitle + " < show more >", "", "", "", "", "", "", "", "", ""]
            });

        }

        this.fetchData = function () {
            var config = {
                params: {
                    //breakdowns: 'ad_group,age,date',
                    //ranges: '1|10,1|4,1|4',
                    breakdowns: 'ad_group,age',
                    ranges: '1|10,1|4',
                },
            };

            var url = '/api/experimental/stats/testdata/';
            $http.get(url, config).success(function (data, status) {
                that.rows = parseData(data.data);
            }).error(function (data, status, headers, config) {
                console.log('ERROR: ' + status);
            });
        };

        this.fetchMore = function () {
            var config = {
                params: {
                    breakdowns: 'ad_group,age,date',
                    ranges: '1|2,1|2,4|7',
                },
            };

        }


        this.fetchData();
    }

    return DataSource;
}]);
