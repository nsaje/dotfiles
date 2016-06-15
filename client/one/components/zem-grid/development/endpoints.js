/* globals oneApp, angular */
/* eslint-disable camelcase */
'use strict';

oneApp.factory('zemGridDebugEndpoint', ['$rootScope', '$controller', '$http', '$q', '$timeout', 'config', function ($rootScope, $controller, $http, $q, $timeout, config) { // eslint-disable-line max-len

    function MockEndpoint (metaData) {
        this.getMetaData = function () {
            var deferred = $q.defer();
            deferred.resolve(metaData);
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
    // Mocked MetaData Definition
    //

    var BREAKDOWN_GROUPS = [
        {name: 'Base level', breakdowns: [{name: 'Base level', query: 'base_level'}]},
        {name: 'Group 1',    breakdowns: [{name: 'By Age', query: 'age'}]},
        {name: 'Group 2',    breakdowns: [{name: 'By Sex', query: 'sex'}]},
        {name: 'Group 3',    breakdowns: [{name: 'By Date', query: 'date'}]},
    ];

    var COLUMNS = {
        base_level: {
            name: 'Mocked Level',
            type: 'breakdownName',
            help: 'Mocked level.',
            shown: true,
            checked: true,
            unselectable: false,
        },
        thumbnail: {
            name: 'Thumbnail',
            type: 'image',
            shown: true,
            checked: true,
            unselectable: false,
        },
        status: {
            name: 'Status',
            type: 'text',
            help: 'Status of an account (enabled or paused).',
            shown: true,
            checked: true,
            unselectable: false,
        },
        performance: {
            nameCssClass: 'performance-icon',
            type: 'icon-list',
            help: 'Goal performance indicator',
            shown: true,
            checked: true,
            unselectable: true,
        },
        submission_status: {
            name: 'Submission Status',
            type: 'submissionStatus',
            help: 'Current submission status.',
            shown: true,
            checked: true,
            unselectable: false,
        },
        default_account_manager: {
            name: 'Account Manager',
            type: 'text',
            help: 'Account manager responsible for the campaign and the communication with the client.',
            shown: true,
            checked: true,
            unselectable: false,
        },
        cost: {
            name: 'Spend',
            type: 'currency',
            help: 'Amount spent per account',
            shown: true,
            checked: true,
            unselectable: false,
        },
        pacing: {
            name: 'Pacing',
            type: 'percent',
            help: '',
            shown: true,
            checked: true,
            unselectable: false,
        },
        clicks: {
            name: 'Clicks',
            type: 'number',
            help: 'The number of times a content ad has been clicked.',
            shown: true,
            checked: true,
            unselectable: false,
        },
        time_on_site: {
            name: 'Time on Site',
            type: 'seconds',
            shown: true,
            checked: true,
            unselectable: false,
        },
        last_sync: {
            name: 'Last OK Sync (EST)',
            type: 'datetime',
            help: 'Dashboard reporting data is synchronized on an hourly basis.',
            shown: true,
            checked: true,
            unselectable: false,
        },
        text_with_popup: {
            name: 'Text with Popup',
            type: 'textWithPopup',
            help: 'Test text with popup.',
            shown: true,
            checked: true,
            unselectable: false,
        },
        test_link_with_icon: {
            name: 'Link with Icon',
            type: 'link',
            shown: true,
            checked: true,
            unselectable: false,
        },
        text_visible_link: {
            name: 'Visible Link',
            type: 'visibleLink',
            shown: true,
            checked: true,
            unselectable: false,
        },
        test_link_text: {
            name: 'Link Text',
            type: 'linkText',
            shown: true,
            checked: true,
            unselectable: false,
        },
        test_link_nav: {
            name: 'Link Nav',
            type: 'linkNav',
            shown: true,
            checked: true,
            unselectable: false,
        },
        test_click_permission_or_text: {
            name: 'Click Permissions',
            type: 'clickPermissionOrText',
            hasPermission: true,
            shown: true,
            checked: true,
            unselectable: false,
        },
        status_setting: {
            name: 'State',
            type: 'state',
            enabledValue: 'Enabled',
            pausedValue: 'Paused',
            onChange: function () {
                return false;
            },
            enablingAutopilotSourcesNotAllowed: function () {
                return false;
            },
            getDisabledMessage: function () {
                return 'Disabled.';
            },
        },
    };

    function getMockedBreakdownGroups () {
        return angular.copy(BREAKDOWN_GROUPS);
    }

    function getMockedCategories () {
        return [
            {
                'name': '1st category',
                fields: [
                    'base_level',
                    'thumbnail',
                    'status',
                    'performance',
                    'submission_status',
                    'status_setting',
                    'default_account_manager',
                    'cost',
                    'pacing',
                    'clicks',
                ],
            },
            {
                'name': '2nd category',
                fields: [
                    'time_on_site',
                    'last_sync',
                    'text_with_popup',
                    'test_link_with_icon',
                    'text_visible_link',
                    'test_link_text',
                    'test_link_nav',
                    'test_click_permission_or_text',
                ],
            },
        ];
    }

    function getMockedColumns () {
        return getColumnsForFields([
            'base_level',
            'thumbnail',
            'status',
            'performance',
            'submission_status',
            'status_setting',
            'default_account_manager',
            'cost',
            'pacing',
            'clicks',
            'time_on_site',
            'last_sync',
            'text_with_popup',
            'test_link_with_icon',
            'text_visible_link',
            'test_link_text',
            'test_link_nav',
            'test_click_permission_or_text',
        ]);
    }

    function getColumnsForFields (fields) {
        var columns = [];
        fields.forEach(function (field) {
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
    var TEST_BREAKDOWNS_BASE_LEVEL = ['General Mills', 'BuildDirect', 'Allstate', 'Clean Energy Experts (Home Solar Programs)', 'Quicken', 'Cresco Labs', 'Macadamia Professional LLC', 'Microsoft']; // eslint-disable-line max-len
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
                query: b.query,
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

    function getBreakdownKeys (breakdown) {
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
        };

        keys = keys.slice(keysFrom, keysTo + 1);

        return [keys, pagination];
    }

    function generateStats (key) {
        var stats = {};

        mockedColumns.forEach(function (column) {
            var value;
            if (column.type === 'breakdownName') {
                value = key;
            } else {
                value = generateRandomValue(column.type, column.field, key);
            }
            stats[column.field] = value;
        });

        return stats;
    }

    /* eslint-disable complexity */
    function generateRandomValue (type, field, key) {
        var value;

        switch (type) {
        case 'text':
            if (field === 'status') {
                value = getMockedStatus();
            } else if (field === 'default_account_manager') {
                value = getMockedAccountManager();
            } else {
                value = 'abcde';
            }
            break;
        case 'number':
            value = getMockedNumber(key === 'Total');
            break;
        case 'currency':
            value = getMockedCurrency(key === 'Total');
            break;
        case 'percent':
            value = getMockedPercentage();
            break;
        case 'seconds':
            value = getMockedSeconds();
            break;
        case 'datetime':
            value = getMockedDateTime();
            break;
        case 'link':
        case 'visibleLink':
        case 'linkText':
            value = getMockedExternalLink(type);
            break;
        case 'linkNav':
            value = getMockedInternalLink();
            break;
        case 'clickPermissionOrText':
            value = getMockedAction();
            break;
        case 'image':
            value = getMockedImage();
            break;
        case 'submissionStatus':
            value = getMockedSubmissionStatus();
            break;
        case 'icon-list':
            value = getMockedIcon();
            break;
        case 'state':
            value = getMockedState();
            break;
        case 'textWithPopup':
            value = getMockedTextWithPopup();
            break;
        }

        return value;
    }
    /* eslint-enable complexity */

    function getMockedStatus () {
        var statuses = ['Active', 'Paused', 'Archived'];
        return statuses[Math.floor(Math.random() * statuses.length)];
    }

    function getMockedAccountManager () {
        var managers = ['Ana Dejanović', 'Tadej Pavlič', 'Chad Lloyd', 'Louis Calderon', 'Helen Wagner', ''];
        return managers[Math.floor(Math.random() * managers.length)];
    }

    function getMockedNumber (isTotal) {
        if (Math.random() < 0.6) {
            var randomNumber = Math.floor(Math.random() * 10000);
            if (isTotal) {
                randomNumber *= 10000;
            }
            return randomNumber;
        }
    }

    function getMockedCurrency (isTotal) {
        if (Math.random() < 0.6) {
            var randomNumber = (Math.random() * 1000000 | 0) / 100;
            if (isTotal) {
                randomNumber *= 10000;
            }
            return randomNumber;
        }
    }

    function getMockedPercentage () {
        if (Math.random() < 0.6) {
            return Math.random() * 400;
        }
    }

    function getMockedSeconds () {
        if (Math.random() < 0.6) {
            return Math.random() * 100;
        }
    }

    function getMockedDateTime () {
        if (Math.random() < 0.6) {
            return getRandomTimestamp(new Date(2016, 0, 1), new Date());
        }
    }

    function getMockedExternalLink (type) {
        var mockedExternalLink;
        switch (type) {
        case 'link':
            if (Math.random() < 0.6) {
                mockedExternalLink = {
                    url: '/?random_link=' + Math.floor(Math.random() * 10000),
                    text: '',
                    icon: config.static_url + '/one/img/link.svg',
                    title: 'Random link with icon.',
                    showDisabled: true,
                    disabledMessage: 'No link here.',
                };
            } else {
                mockedExternalLink = {
                    url: '',
                    text: '',
                    icon: config.static_url + '/one/img/link.svg',
                    title: 'Disabled link with icon.',
                    showDisabled: true,
                    disabledMessage: 'Should be visible.',
                };
            }
            return mockedExternalLink;
        case 'visibleLink':
            if (Math.random() < 0.6) {
                mockedExternalLink = {
                    url: '/?random_link=' + Math.floor(Math.random() * 10000),
                    text: '',
                    icon: config.static_url + '/one/img/link.svg',
                    title: 'Should be visible.',
                    showDisabled: false,
                    disabledMessage: '',
                };
            } else {
                mockedExternalLink = {
                    text: '',
                    icon: config.static_url + '/one/img/link.svg',
                    title: 'Should be hidden.',
                    showDisabled: false,
                    disabledMessage: '',
                };
            }
            return mockedExternalLink;
        case 'linkText':
            if (Math.random() < 0.6) {
                mockedExternalLink = {
                    url: '/?random_link=' + Math.floor(Math.random() * 10000),
                    text: 'Link with text',
                    icon: '',
                    title: 'Link with text.',
                    showDisabled: true,
                    disabledMessage: '',
                };
            } else {
                mockedExternalLink = {
                    url: '',
                    text: 'No link with text',
                    icon: '',
                    title: 'No link with text.',
                    showDisabled: true,
                    disabledMessage: '',
                };
            }
            return mockedExternalLink;
        }
    }

    function getMockedInternalLink () {
        return {
            state: 'main.accounts.campaigns',
            id: 118,
            text: 'Test link nav',
        };
    }

    function getMockedAction () {
        return 'Test click permission or text';
    }

    function getMockedImage () {
        var images = [
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
        var randomImage = images[Math.floor(Math.random() * images.length)];
        return {
            square: 'https://images2.zemanta.com/' + randomImage + '?w=160&h=160&fit=crop&crop=faces&fm=jpg',
            landscape: 'https://images2.zemanta.com/' + randomImage + '?w=256&h=160&fit=crop&crop=faces&fm=jpg',
        };
    }

    function getMockedSubmissionStatus () {
        return {
            statusItems: [
                {status: 1, text: 'Pending', name: 'Sharethrough', source_state: ''},
                {status: 2, text: 'Approved', name: 'TripleLift', source_state: ''},
                {status: 3, text: 'Rejected (Title too long)', name: 'Yahoo', source_state: ''},
            ],
        };
    }

    function getMockedIcon () {
        var rnd = Math.random();
        if (rnd < 0.25) {
            return {list: [{emoticon: 1, text: '$0.201 CPC (planned $0.350)'}], overall: 1};
        } else if (rnd < 0.5) {
            return {list: [{emoticon: 2, text: 'N/A CPC (planned $0.350)'}], overall: 2};
        } else if (rnd < 0.75) {
            return {list: [{emoticon: 3, text: 'N/A CPC (planned $0.350)'}], overall: 3};
        }
    }

    function getMockedState () {
        return Math.floor(Math.random() * 3 + 1);
    }

    function getMockedTextWithPopup () {
        return {
            text: 'Random text',
            popupContent: 'ಠᴗಠ',
        };
    }

    function getRandomTimestamp (start, end) {
        return new Date(start.getTime() + Math.random() * (end.getTime() - start.getTime())).getTime();
    }

    function createMetaData () {
        return {
            columns: getMockedColumns(),
            categories: getMockedCategories(),
            breakdownGroups: getMockedBreakdownGroups(),
            localStoragePrefix: 'zem-data-source-debug-endpoint',
        };
    }

    function createEndpoint (metaData) {
        if (!metaData) metaData = createMetaData();
        return new MockEndpoint(metaData);
    }

    return {
        createMetaData: createMetaData,
        createEndpoint: createEndpoint,
    };
}]);
