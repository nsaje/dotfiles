/* eslint-disable camelcase */

angular
    .module('one.widgets')
    .factory('zemGridDebugEndpoint', function(
        $rootScope,
        $controller,
        $http,
        $q,
        $timeout,
        zemGridConstants
    ) {
        // eslint-disable-line max-len

        function MockEndpoint(metaData) {
            this.getMetaData = function() {
                var deferred = $q.defer();
                deferred.resolve(metaData);
                return deferred.promise;
            };

            this.getData = function(config) {
                var deferred = $q.defer();
                var timer = $timeout(function() {
                    var data = generateData(config);
                    deferred.promise.abort = angular.noop;
                    deferred.resolve(data);
                }, 500 + (config.level - 1) * 500);

                deferred.promise.abort = function() {
                    $timeout.cancel(timer);
                    deferred.reject();
                };

                return deferred.promise;
            };

            this.saveData = function(value, row, column) {
                var deferred = $q.defer();
                row.stats[column.field].value = value;
                deferred.resolve({
                    rows: [row],
                });
                return deferred.promise;
            };
        }

        // ///////////////////////////////////////////////////////////////////////////////////////////
        // Mocked MetaData Definition
        //

        var BREAKDOWN_GROUPS = {
            base: {
                name: 'Base level',
                breakdowns: [{name: 'Base level', query: 'base_level'}],
            },
            age: {
                name: 'Group 1',
                breakdowns: [{name: 'By Age', query: 'age'}],
            },
            gender: {
                name: 'Group 2',
                breakdowns: [{name: 'By Sex', query: 'sex'}],
            },
            time: {
                name: 'Group 3',
                breakdowns: [{name: 'By Date', query: 'date'}],
            },
        };

        var COLUMNS = {
            breakdown_name: {
                name: 'Mocked Level',
                type: zemGridConstants.gridColumnTypes.BREAKDOWN,
                help: 'Mocked level.',
                order: true,
                shown: true,
                checked: true,
                unselectable: false,
            },
            thumbnail: {
                name: 'Thumbnail',
                type: zemGridConstants.gridColumnTypes.THUMBNAIL,
                order: true,
                shown: true,
                checked: true,
                unselectable: false,
            },
            status: {
                name: 'Status',
                type: zemGridConstants.gridColumnTypes.STATUS,
                help: 'Status of an account (enabled or paused).',
                order: true,
                shown: true,
                checked: true,
                unselectable: false,
            },
            performance: {
                nameCssClass: 'performance-icon',
                type: zemGridConstants.gridColumnTypes.PERFORMANCE_INDICATOR,
                help: 'Goal performance indicator',
                order: true,
                shown: true,
                checked: true,
                unselectable: true,
            },
            submission_status: {
                name: 'Submission Status',
                type: zemGridConstants.gridColumnTypes.SUBMISSION_STATUS,
                help: 'Current submission status.',
                order: true,
                shown: true,
                checked: true,
                unselectable: false,
            },
            default_account_manager: {
                name: 'Account Manager',
                type: zemGridConstants.gridColumnTypes.TEXT,
                help:
                    'Account manager responsible for the campaign and the communication with the client.',
                order: true,
                shown: true,
                checked: true,
                unselectable: false,
            },
            cost: {
                name: 'Spend',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                help: 'Amount spent per account',
                order: true,
                shown: true,
                checked: true,
                unselectable: false,
                fractionSize: 2,
                isEdtable: true,
            },
            pacing: {
                name: 'Pacing',
                type: zemGridConstants.gridColumnTypes.PERCENT,
                help: '',
                shown: true,
                checked: true,
                unselectable: false,
            },
            clicks: {
                name: 'Clicks',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                help: 'The number of times a content ad has been clicked.',
                shown: true,
                checked: true,
                unselectable: false,
            },
            time_on_site: {
                name: 'Time on Site',
                type: zemGridConstants.gridColumnTypes.SECONDS,
                shown: true,
                checked: true,
                unselectable: false,
            },
            last_sync: {
                name: 'Last OK Sync (EST)',
                type: zemGridConstants.gridColumnTypes.DATE_TIME,
                help:
                    'Dashboard reporting data is synchronized on an hourly basis.',
                shown: true,
                checked: true,
                unselectable: false,
            },
        };

        function getMockedBreakdownGroups() {
            return angular.copy(BREAKDOWN_GROUPS);
        }

        function getMockedCategories() {
            return [
                {
                    name: '1st category',
                    fields: [
                        'breakdown_name',
                        'thumbnail',
                        'status',
                        'performance',
                        'submission_status',
                        'default_account_manager',
                        'cost',
                        'pacing',
                        'clicks',
                    ],
                },
                {
                    name: '2nd category',
                    fields: ['time_on_site', 'last_sync'],
                },
            ];
        }

        function getMockedColumns() {
            return getColumnsForFields([
                'breakdown_name',
                'thumbnail',
                'performance',
                'submission_status',
                'default_account_manager',
                'cost',
                'pacing',
                'clicks',
                'time_on_site',
                'last_sync',
            ]);
        }

        function getColumnsForFields(fields) {
            var columns = [];
            fields.forEach(function(field) {
                var column = angular.copy(COLUMNS[field]);
                column.field = field;
                columns.push(column);
            });
            return columns;
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

        var mockedColumns = getMockedColumns();

        var TEST_BREAKDOWNS_AGES = [
            '<18',
            '18-21',
            '21-30',
            '30-40',
            '40-50',
            '50-60',
            '60-70',
            '70-80',
            '80-90',
            '99+',
        ];
        var TEST_BREAKDOWNS_SEX = ['man', 'woman'];
        var TEST_BREAKDOWNS_BASE_LEVEL = [
            'General Mills',
            'BuildDirect',
            'Allstate',
            'Clean Energy Experts (Home Solar Programs)',
            'Quicken',
            'Cresco Labs',
            'Macadamia Professional LLC',
            'Microsoft',
            'Happy Feet Dragons',
            'Fishy Mishy Mu',
        ]; // eslint-disable-line max-len
        var TEST_BREAKDOWNS_DATES = [];

        while (TEST_BREAKDOWNS_BASE_LEVEL.length < 100) {
            TEST_BREAKDOWNS_BASE_LEVEL = TEST_BREAKDOWNS_BASE_LEVEL.concat(
                TEST_BREAKDOWNS_BASE_LEVEL
            );
        }
        for (var i = 0; i < 30; ++i) {
            var d = '2015-03-' + (i + 1);
            TEST_BREAKDOWNS_DATES.push(d);
        }

        function generateData(config) {
            var breakdowns = getBreakdownRanges(config);
            var topLevelRow = generateRandomBreakdown(breakdowns);
            topLevelRow.breakdown.totals = topLevelRow.stats;
            var topLevelBreakdown = {
                rows: [topLevelRow],
                level: 0,
            };

            return getBreakdownsForLevel(topLevelBreakdown, config.level, true);
        }

        function getBreakdownRanges(config) {
            var range = []; // [[min,max], ...]
            for (var i = 0; i < config.level - 1; ++i) {
                range.push([1000, 0]);
            }

            config.breakdownParents.forEach(function(breakdownId) {
                var position = JSON.parse(breakdownId);
                for (var i = 0; i < config.level - 1; ++i) {
                    range[i][0] = Math.min(range[i][0], position[i + 1]);
                    range[i][1] = Math.max(range[i][1], position[i + 1]);
                }
            });

            range.push([config.offset, config.offset + config.limit - 1]);

            return config.breakdown.map(function(b, i) {
                return {
                    query: b.query,
                    range: range[i],
                };
            });
        }

        function getBreakdownsForLevel(breakdown, level, flat) {
            var breakdowns = [breakdown];
            for (var i = 0; i < level; ++i) {
                var nestedBreakdowns = [];
                breakdowns.forEach(function(breakdown) {
                    breakdown.rows.forEach(function(row) {
                        nestedBreakdowns.push(row.breakdown);
                    });
                });
                breakdowns = nestedBreakdowns;
            }
            if (flat) {
                breakdowns.forEach(function(breakdown) {
                    breakdown.rows.forEach(function(row) {
                        delete row.breakdown;
                    });
                });
            }
            return breakdowns;
        }

        function generateRandomBreakdown(breakdowns, level, position, key) {
            if (!level) level = 1;
            if (!position) position = [0];
            if (!key) key = 'Total';

            var row = {
                stats: generateStats(key),
                breakdownId: JSON.stringify(position),
                archived: Math.random() < 0.3,
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

                keys.forEach(function(k, idx) {
                    var childPosition = position.slice(0);
                    childPosition.push(pagination.offset + idx);
                    var r = generateRandomBreakdown(
                        breakdowns,
                        level + 1,
                        childPosition,
                        k
                    );
                    rows.push(r);
                });
            }

            return row;
        }

        function getBreakdownKeys(breakdown) {
            var keys = null;
            switch (breakdown.query) {
                case 'date':
                    keys = TEST_BREAKDOWNS_DATES;
                    break;
                case 'age':
                    keys = TEST_BREAKDOWNS_AGES;
                    break;
                case 'base_level':
                    keys = TEST_BREAKDOWNS_BASE_LEVEL;
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
                complete: keysCount === keysTo,
            };

            keys = keys.slice(keysFrom, keysTo + 1);

            return [keys, pagination];
        }

        function generateStats(key) {
            var stats = {};

            mockedColumns.forEach(function(column) {
                var data;
                if (column.field === 'breakdown_name') {
                    data = {
                        value: key,
                    };
                } else {
                    data = generateRandomData(column.type, column.field, key);
                }
                stats[column.field] = data;
            });

            return stats;
        }

        /* eslint-disable complexity */
        function generateRandomData(type, field, key) {
            var data;

            switch (type) {
                case zemGridConstants.gridColumnTypes.TEXT:
                    if (field === 'default_account_manager') {
                        data = getMockedAccountManager();
                    } else {
                        data = 'abcde';
                    }
                    break;
                case zemGridConstants.gridColumnTypes.STATUS:
                    data = getMockedStatus();
                    break;
                case zemGridConstants.gridColumnTypes.NUMBER:
                    data = getMockedNumber(key === 'Total');
                    break;
                case zemGridConstants.gridColumnTypes.CURRENCY:
                    data = getMockedCurrency(key === 'Total');
                    break;
                case zemGridConstants.gridColumnTypes.PERCENT:
                    data = getMockedPercentage();
                    break;
                case zemGridConstants.gridColumnTypes.SECONDS:
                    data = getMockedSeconds();
                    break;
                case zemGridConstants.gridColumnTypes.DATE_TIME:
                    data = getMockedDateTime();
                    break;
                case zemGridConstants.gridColumnTypes.THUMBNAIL:
                    data = getMockedThumbnail();
                    break;
                case zemGridConstants.gridColumnTypes.SUBMISSION_STATUS:
                    data = getMockedSubmissionStatus();
                    break;
                case zemGridConstants.gridColumnTypes.PERFORMANCE_INDICATOR:
                    data = getMockedPerformance();
                    break;
            }

            return data;
        }
        /* eslint-enable complexity */

        function getMockedStatus() {
            return {
                value: Math.floor(Math.random() * 3),
            };
        }

        function getMockedAccountManager() {
            var managers = [
                'Ana Dejanović',
                'Tadej Pavlič',
                'Chad Lloyd',
                'Louis Calderon',
                'Helen Wagner',
                '',
            ];
            return {
                value: managers[Math.floor(Math.random() * managers.length)],
            };
        }

        function getMockedNumber(isTotal) {
            if (Math.random() < 0.6) {
                var randomNumber = Math.floor(Math.random() * 10000);
                if (isTotal) {
                    randomNumber *= 10000;
                }
                return {
                    value: randomNumber,
                };
            }
        }

        function getMockedCurrency(isTotal) {
            if (Math.random() < 0.6) {
                var randomNumber = ((Math.random() * 1000000) | 0) / 100;
                if (isTotal) {
                    randomNumber *= 10000;
                }
                return {
                    value: randomNumber,
                };
            }
        }

        function getMockedPercentage() {
            if (Math.random() < 0.6) {
                return {
                    value: Math.random() * 400,
                };
            }
        }

        function getMockedSeconds() {
            if (Math.random() < 0.6) {
                return {
                    value: Math.random() * 100,
                };
            }
        }

        function getMockedDateTime() {
            if (Math.random() < 0.6) {
                return {
                    value: getRandomTimestamp(new Date(2016, 0, 1), new Date()),
                };
            }
        }

        function getMockedThumbnail() {
            var thumbnails = [
                'ff36fcbc-64b0-419c-bf56-346778f6fd4b.jpg',
                '725f638c-e8a4-4ff9-a2f2-3783971d98d3.jpg',
                '2fbbf448-8988-4617-854b-53d3ab2260e0.jpg',
                'efdda23c-5d57-4842-808a-963554b0d3d9.jpg',
                '6daa9ae4-f8d4-49e1-86db-058f9a9fb91b.jpg',
                '09f44654-f8a9-4a77-abc8-667f9e5ed0e3.jpg',
                '58bb0b05-83aa-481d-b0a1-9e94c3b076b5.jpg',
                'aeaaaf0e-62a4-41f7-a4bf-92f6d8fa7549.jpg',
                'e325b27c-2330-4c0e-ba4b-c5d76c742439.jpg',
                '18b47c2f-ac70-4e75-a9d5-82b6f7a79d6e.jpg',
            ];
            if (Math.random() < 0.6) {
                var randomThumbnail =
                    thumbnails[Math.floor(Math.random() * thumbnails.length)];
                return {
                    square:
                        'https://images2.zemanta.com/' +
                        randomThumbnail +
                        '?w=160&h=160&fit=crop&crop=faces&fm=jpg',
                    landscape:
                        'https://images2.zemanta.com/' +
                        randomThumbnail +
                        '?w=256&h=160&fit=crop&crop=faces&fm=jpg',
                };
            }
        }

        var submissionStatusIndex = 0;
        function getMockedSubmissionStatus() {
            var statuses = [];
            for (var i = 0; i < submissionStatusIndex; i++) {
                statuses.push({
                    status: 2,
                    text: 'Approved',
                    name: 'Source ' + i,
                    source_state: '',
                });
            }
            statuses.push({
                status: 1,
                text: 'Pending',
                name: 'Pending Source',
                source_state: '',
            });
            statuses.push({
                status: 3,
                text: 'Rejected (Title too long)',
                name: 'Rejected Source',
                source_state: '',
            });
            submissionStatusIndex++;
            return statuses;
        }

        var performanceIndicatorIndex = 0;
        function getMockedPerformance() {
            var rnd = Math.random();
            if (rnd < 0.25) {
                return {
                    list: [
                        {
                            emoticon: 1,
                            text:
                                '$0.201 CPC (planned $0.350), index: ' +
                                performanceIndicatorIndex++,
                        },
                    ],
                    overall: 1,
                };
            } else if (rnd < 0.5) {
                return {
                    list: [
                        {
                            emoticon: 2,
                            text:
                                'N/A CPC (planned $0.350), index: ' +
                                performanceIndicatorIndex++,
                        },
                    ],
                    overall: 2,
                };
            } else if (rnd < 0.75) {
                return {
                    list: [
                        {
                            emoticon: 3,
                            text:
                                'N/A CPC (planned $0.350), index: ' +
                                performanceIndicatorIndex++,
                        },
                    ],
                    overall: 3,
                };
            }
        }

        function getRandomTimestamp(start, end) {
            return new Date(
                start.getTime() +
                    Math.random() * (end.getTime() - start.getTime())
            ).getTime();
        }

        function createMetaData() {
            return {
                columns: getMockedColumns(),
                categories: getMockedCategories(),
                breakdownGroups: getMockedBreakdownGroups(),
            };
        }

        function createEndpoint(metaData) {
            if (!metaData) metaData = createMetaData();
            return new MockEndpoint(metaData);
        }

        return {
            createMetaData: createMetaData,
            createEndpoint: createEndpoint,
        };
    });
