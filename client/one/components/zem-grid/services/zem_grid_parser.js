/* globals oneApp */
'use strict';

oneApp.factory('zemGridParser', ['$filter', 'zemGridConstants', 'zemGridObject', function ($filter, zemGridConstants, zemGridObject) { // eslint-disable-line max-len

    //
    // Service responsible for parsing Breakdown data (tree) to Grid rows
    // It flattens tree so that Grid is functioning on rows[] array.
    // All basic data types are parsed here to overcome the need for filters in templates
    //    ie. stats where (string) -> (string) conversion is possible
    //    types: number, currency, percent, seconds, datetime
    //

    function parse (grid, data) {
        if (data.level > 0) throw 'Inplace parsing not supported yet.';

        if (data.breakdown) {
            grid.footer.row = zemGridObject.createRow(zemGridConstants.gridRowType.STATS, data, 0);
            grid.footer.row.stats = parseStats(grid, data.stats);
            grid.body.rows = parseBreakdown(grid, null, data.breakdown);
        } else {
            grid.body.rows = [];
            grid.footer.stats = null;
        }
    }

    function parseBreakdown (grid, parent, breakdown) {
        var rows = [];
        var level = breakdown.level;

        breakdown.rows.forEach(function (data) {
            var row = zemGridObject.createRow(zemGridConstants.gridRowType.STATS, data, level, parent);
            row.stats = parseStats(grid, data.stats);
            rows.push(row);
            if (data.breakdown) {
                var breakdownRows = parseBreakdown(grid, row, data.breakdown);
                rows = rows.concat(breakdownRows);
            }
        });

        var row = zemGridObject.createRow(zemGridConstants.gridRowType.BREAKDOWN, breakdown, level, parent);

        // TODO: refactor (move to virtual scroll functionality)
        // HACK: Empty stats for render optimizations (ng-repeat, ng-switch)
        var emptyStats = {};
        grid.meta.data.columns.forEach(function (col) {
            emptyStats[col.field] = '';
        });
        row.data.stats = emptyStats;
        rows.push(row);

        return rows;
    }

    function parseStats (grid, stats) {
        // Parse (pre-filter) all stats that does not require special handling to remove the
        // need for filters in the templates (huge performance gain). If field can't be parsed
        // here just use the same value as in data stats
        var parsedStats = {};
        grid.meta.data.columns.forEach(function (col) {
            var parsedValue;
            switch (col.type) {
            case 'percent': parsedValue = parsePercent(stats[col.field], col); break;
            case 'number': parsedValue = parseNumber(stats[col.field], col); break;
            case 'currency': parsedValue = parseCurrency(stats[col.field], col); break;
            case 'seconds': parsedValue = parseSeconds(stats[col.field], col); break;
            case 'datetime': parsedValue = parseDateTime(stats[col.field], col); break;
            default: parsedValue = stats[col.field];
            }
            parsedStats[col.field] = parsedValue;
        });
        return parsedStats;
    }

    function parsePercent (value) {
        if (value !== 0 && !value) return 'N/A';
        return $filter('number')(value, 2) + '%';
    }

    function parseSeconds (value) {
        if (value !== 0 && !value) return 'N/A';
        return $filter('number')(value, 1) + ' s';
    }

    function parseDateTime (value) {
        if (!value) return 'N/A';
        return $filter('date')(value, 'M/d/yyyy h:mm a');
    }

    function parseNumber (value, column) {
        if (value !== 0 && !value) return 'N/A';
        var fractionSize = column.fractionSize || 0;
        return $filter('number')(value, fractionSize);
    }

    function parseCurrency (value, column) {
        if (value !== 0 && !value) return 'N/A';
        var fractionSize = column.fractionSize || 0;
        return $filter('decimalCurrency')(value, '$', fractionSize, '');
    }

    return {
        parse: parse,
    };
}]);
