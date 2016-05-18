/* globals oneApp */
'use strict';

oneApp.factory('zemGridParser', ['$q', 'zemGridConstants', function ($q, zemGridConstants) {

    function parse (grid, data) {
        // Level 0 -> total data and level 1 breakdown
        var totals = data.rows[0];
        var breakdown = totals.breakdown;

        grid.footer = {type: zemGridConstants.gridRowType.STATS, level: 0, data: totals, visible: true};
        grid.body.rows = parseBreakdown(null, breakdown);
    }

    function parseInplace (grid, row, data) {
        var rows = parseBreakdown(row.parent, data);
        rows.pop();
        var idx = grid.body.rows.indexOf(row);
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
                parent: parent,
                visible: true,
                collapsed: false,
            };
            rows.push(row);
            if (data.breakdown) {
                var breakdownRows = parseBreakdown(row, data.breakdown);
                rows = rows.concat(breakdownRows);
            }
        });

        var row = {
            type: zemGridConstants.gridRowType.BREAKDOWN,
            level: level,
            data: breakdown,
            parent: parent,
            visible: true,
        };
        rows.push(row);

        return rows;
    }

    return  {
        parse: parse,
        parseInplace: parseInplace,
    };
}]);
