/*globals angular,oneApp,constants,options,moment*/
'use strict';

oneApp.factory('zemDataSourceService', [function () {


    function DataSource () {
        this.columns = ['Name', 'Stat 1', 'Stat 2', 'Stat 3', 'Stat 4'];
        this.rows = [
            ['a', 1, 2, 3, 4],
            ['b', 1, 2, 3, 4],
            ['c', 1, 2, 3, 4],
            ['d', 1, 2, 3, 4],
            ['Total', 4, 8, 12, 16],
        ];

    }
    return DataSource;
}]);
