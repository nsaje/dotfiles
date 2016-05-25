/* globals oneApp */
'use strict';

oneApp.factory('zemDataSourceDebugEndpoints', ['$rootScope', '$controller', '$http', '$q', '$timeout', function ($rootScope, $controller, $http, $q, $timeout) { // eslint-disable-line max-len

    function MockEndpoint () {
        this.availableBreakdowns = ['ad_group', 'age', 'sex', 'date'];
        this.defaultBreakdown = ['ad_group', 'age', 'date'];

        this.getMetaData = function () {
            var deferred = $q.defer();
            deferred.resolve({
                columns: generateColumnsData(),
            });
            return deferred.promise;
        };

        this.getData = function (config) {
            var deferred = $q.defer();
            $timeout(function () {
                var data = generateData(config);
                deferred.resolve(data);
            }, 500 + (config.level - 1) * 500);
            return deferred.promise;
        };
    }

    // ///////////////////////////////////////////////////////////////////////////////////////////
    // Data generator
    //
    //
    // <breakdown>
    //   -> level
    //   -> position - [a,b,c]
    //   -> pagination - from, to, size, count
    //   -> rows []
    //       -> row
    //           -> data
    //           -> <breakdown> - (level + 1)
    //
    // level 0 -> wrapper for total row and it's breakdown
    // level 1 -> first level breakdown - original rows  with potential breakdown
    // level 2-n -> breakdowns
    //

    var TEST_COLUMNS = 20;
    var TEST_BREAKDOWNS_AD_GROUPS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
    var TEST_BREAKDOWNS_AGES = ['<18', '18-21', '21-30', '30-40', '40-50', '50-60', '60-70', '70-80', '80-90', '99+'];
    var TEST_BREAKDOWNS_SEX = ['man', 'woman'];
    var TEST_BREAKDOWNS_DATES = [];
    for (var i = 0; i < 30; ++i) {
        var d = '2015-03-' + (i + 1);
        TEST_BREAKDOWNS_DATES.push(d);
    }

    function generateData (config) {
        var breakdowns = getBreakdownRanges(config);
        var topLevelRow = generateRandomBreakdown(breakdowns);
        topLevelRow.breakdown.totals = topLevelRow.stats;
        var topLevelBreakdown = {
            rows: [topLevelRow],
            level: 0,
        };

        return getBreakdownsForLevel(topLevelBreakdown, config.level, true);
    }

    function getBreakdownRanges (config) {
        var range = []; // [[min,max], ...]
        for (var i = 0; i < config.level - 1; ++i) {
            range.push([1000, 0]);
        }

        config.breakdownPage.forEach(function (breakdownId) {
            var position = JSON.parse(breakdownId);
            for (var i = 0; i < config.level - 1; ++i) {
                range[i][0] = Math.min(range[i][0], position[i + 1]);
                range[i][1] = Math.max(range[i][1], position[i + 1]);
            }
        });

        range.push([config.offset, config.offset + config.limit - 1]);

        return config.breakdown.map(function (b, i) {
            return {
                name: b,
                range: range[i],
            };
        });
    }

    function getBreakdownsForLevel (breakdown, level, flat) {
        var breakdowns = [breakdown];
        for (var i = 0; i < level; ++i) {
            var nestedBreakdowns = [];
            breakdowns.forEach(function (breakdown) {
                breakdown.rows.forEach(function (row) {
                    nestedBreakdowns.push(row.breakdown);
                });
            });
            breakdowns = nestedBreakdowns;
        }
        if (flat) {
            breakdowns.forEach(function (breakdown) {
                breakdown.rows.forEach(function (row) {
                    delete row.breakdown;
                });
            });
        }
        return breakdowns;
    }

    function generateRandomBreakdown (breakdowns, level, position, key) {
        if (!level) level = 1;
        if (!position) position = [0];
        if (!key) key = 'Total';

        var row = {
            stats: generateStats(key),
            breakdownId: JSON.stringify(position),
        };

        if (level <= breakdowns.length) {
            var breakdown = {};
            row.breakdown = breakdown;

            var res = getBreakdownKeys(breakdowns[level - 1]);
            var keys = res[0];
            var pagination = res[1];
            var rows = [];
            breakdown.rows = rows;
            breakdown.pagination = pagination;
            breakdown.level = level;
            breakdown.breakdownId = JSON.stringify(position);

            keys.forEach(function (k, idx) {
                var childPosition = position.slice(0);
                childPosition.push(pagination.offset + idx);
                var r = generateRandomBreakdown(breakdowns, level + 1, childPosition, k);
                rows.push(r);
            });
        }

        return row;
    }

    function generateColumnsData () {
        var columns = [];
        for (var idx = 0; idx < TEST_COLUMNS; idx++) {
            columns.push({
                name: 'Field ' + idx,
                field: 'field' + idx,
            });
        }
        return columns;
    }

    function generateStats (key) {
        var stats = {
            field0: key,
        };

        for (var idx = 1; idx < TEST_COLUMNS; idx++) {
            var val = (Math.random() * 1000000 | 0) / 100;
            if (key === 'Total') {
                val = (Math.random() * 100000000 * 100 | 0) / 100;
            }
            stats['field' + idx] = '' + val;
        }

        return stats;
    }

    function getBreakdownKeys (breakdown) {
        var keys = null;
        switch (breakdown.name) {
        case 'date':
            keys = TEST_BREAKDOWNS_DATES;
            break;
        case 'age':
            keys = TEST_BREAKDOWNS_AGES;
            break;
        case 'ad_group':
            keys = TEST_BREAKDOWNS_AD_GROUPS;
            break;
        case 'sex':
            keys = TEST_BREAKDOWNS_SEX;
            break;
        }

        var keysCount = keys.length;
        var keysFrom = breakdown.range[0];
        var keysTo = Math.min(breakdown.range[1], keysCount);

        if (keysFrom > keysTo || keysFrom < 0) {
            throw 'Out of bounds';
        }

        var pagination = {
            offset: keysFrom,
            limit: keysTo - keysFrom,
            count: keysCount,
        };

        keys = keys.slice(keysFrom, keysTo + 1);

        return [keys, pagination];
    }

    return {
        createMockEndpoint: function () {
            return new MockEndpoint();
        },
    };
}]);
