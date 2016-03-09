/*globals angular,oneApp,constants,options,moment*/
'use strict';

oneApp.factory('zemDataSourceService', ['$http', function ($http) {


    function DataSource () {
        this.columns = ['Name', 'Stat 1', 'Stat 2', 'Stat 3', 'Stat 4'];
        this.rows = [ ];

        this.parseData = function(data){
            this.rows = [];
            this.parseBreakdown(data.breakdown, this.rows, 1);

            var options = { type: 0, level: 0 };
            this.rows.push({options: options, data: data.data});
        };

        this.parseBreakdown = function(breakdown, rows, level){
            angular.forEach(breakdown.rows, function (row) {
                var options = { type: 0, level: level, };

                rows.push({options: options, data: row.data});
                if (row.hasOwnProperty('breakdown')) {
                    that.parseBreakdown (row.breakdown, rows, level + 1);
                }
            });
        };

        var config = {
            params: {
                breakdowns: 'ad_group,age,date',
                ranges: '1|3,1|3,1|3',
            },
        };

        var url = '/api/experimental/stats/testdata/';
        var that = this;
        $http.get(url, config).success(function (data, status){
            that.parseData(data.data);
        }).
        error(function (data, status, headers, config) {
            console.log('ERROR: ' + status);
        });


    }
    return DataSource;
}]);
