/* globals oneApp */
'use strict';

oneApp.factory('zemGridUtil', ['zemGridConstants', function (zemGridConstants) { // eslint-disable-line max-len

    var columns = ['Name', 'Short stat', 'Looooogner stat', 'Realy looooooooooong stat', 'A', 'B', 'C', 'AA', 'BB', 'CC', 'AAA', 'BBB', 'CCC', 'AAAA', 'BBBB', 'CCCC', 'AAAAA', 'BBBBB', 'CCCCC', 'ZZZZZ'];

    function parseMetaData(data) {
        var grid = {
            header: {columns: columns},
            body: {rows: []},
            footer: {data: []}
        };

        return grid;
    }

    function parseData(grid, data) {
        // Level 0 -> total data and level 1 breakdown
        var totals = data.rows[0];
        var breakdown = totals.breakdown;

        grid.footer = { type: zemGridConstants.gridRowType.STATS, level: 0, data: totals};
        grid.body.rows = parseBreakdown(null, breakdown);
    }

    function parseDataInplace(grid, row, data) {
        var rows = $scope.parseBreakdown(row.parent, data);
        var idx = $scope.rows.indexOf(row);
        rows.pop();
        grid.body.rows.splice.apply(grid.body.rows, [idx, 0].concat(rows));
    }

    function parseBreakdown (parent, breakdown) {
        var rows = [];
        var level = breakdown.level;

        breakdown.rows.forEach(function (data) {
            var row = {
                type: zemGridConstants.gridRowType.STATS,
                level: level,
                data: data,
                parent: parent
            };
            rows.push(row);
            if (data.breakdown) {
                var breakdownRows = $scope.parseBreakdown(row, data.breakdown);
                rows = rows.concat(breakdownRows);
            }
        });

        var row = {
            type: zemGridConstants.gridRowType.BREAKDOWN,
            level: level,
            data: breakdown,
            parent: parent
        };
        rows.push(row);

        return rows;
    }


    return {
        parseMetaData: parseMetaData,
        parseData: parseData,
        parseDataInplace: parseDataInplace,
    }
}
