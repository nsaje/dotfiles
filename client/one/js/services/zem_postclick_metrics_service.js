/*globals angular,oneApp,options,moment*/
"use strict";

oneApp.factory('zemPostclickMetricsService', function() {
    function insertColumns(columns, isInternal) {
        columns.splice(columns.length - 1, 0, {
            name: 'Visits',
            field: 'visits',
            checked: true,
            type: 'number',
            internal: isInternal,
            help: 'Total number of sessions within a date range. A session is the period of time in which a user is actively engaged with your site.',
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        }, {
            name: 'Pageviews',
            field: 'pageviews',
            checked: true,
            type: 'number',
            internal: isInternal,
            help: 'Total number of pageviews made during the selected date range. A pageview is a view of a single page. Repeated views are counted.',
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        }, {
            name: '% New Users',
            field: 'percent_new_users',
            checked: false,
            type: 'percent',
            internal: isInternal,
            help: 'An estimate of first time visits during the selected date range.',
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        }, {
            name: 'Bounce Rate',
            field: 'bounce_rate',
            checked: false,
            type: 'percent',
            internal: isInternal,
            help: 'Percantage of visits that resulted in only one page view.',
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        }, {
            name: 'PV/Visit',
            field: 'pv_per_visit',
            checked: false,
            type: 'number',
            fractionSize: 2,
            internal: isInternal,
            help: 'Average number of pageviews per visit.',
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        }, {
            name: 'Avg. ToS',
            field: 'avg_tos',
            checked: false,
            type: 'seconds',
            internal: isInternal,
            help: 'Average time spent on site in seconds during the selected date range.',
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        }, {
            name: 'Click Discrepancy',
            field: 'click_discrepancy',
            checked: false,
            type: 'percent',
            internal: isInternal,
            help: 'Clicks detected only by media source as a percentage of total clicks.',
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        });
    }

    function concatChartOptions(chartOptions, isInternal) {
        return chartOptions.concat(options.adGroupChartPostClickMetrics.map(function (option) {
            option.internal = isInternal;
            return option;
        }));
    }

    return {
        insertColumns: insertColumns,
        concatChartOptions: concatChartOptions
    }
});
