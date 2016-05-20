/* globals oneApp */
'use strict';

oneApp.factory('zemGridParser', ['$q', 'zemGridConstants', function ($q, zemGridConstants) {

    function parse (grid, data) {
        if (data.level === 0) {
            grid.footer = {type: zemGridConstants.gridRowType.STATS, level: 0, data: data, visible: true};
            grid.body.rows = parseBreakdown(null, data.breakdown);
        } else {
            throw 'Inplace parsing not supported yet.';
        }
    }

    function parseInplace (grid, breakdown) {
        var row = getRow(grid, breakdown);
        var rows = parseBreakdown(row.parent, breakdown);
        rows.pop();
        var idx = grid.body.rows.indexOf(row);
        grid.body.rows.splice.apply(grid.body.rows, [idx, 0].concat(rows));
    }

    function getRow (grid, breakdown) {
        // FIXME
        return grid.body.rows.find(function (row) {
            return row.level == breakdown.level &&
                JSON.stringify(breakdown.position) === JSON.stringify(row.data.position);
        });
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

    return {
        parse: parse,
        parseInplace: parseInplace,
    };
}]);
